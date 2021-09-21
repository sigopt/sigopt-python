from http import HTTPStatus
from kubernetes.client.exceptions import ApiException as KubernetesApiException
import logging
import signal
import threading
from sigopt.run_context import RunContext

from controller.create_pod import create_run_pod
from controller.event_repeater import EventRepeater
from controller.pod_status import is_pod_active
from controller.refill_pods import RefillExperimentPodsThread
from controller.run_state import RunState
from controller.settings import ExperimentSettings, RunSettings
from controller.watch_pods import WatchPodsThread


def create_run_state(sigopt_settings, pod, k8s_settings):
  run_id = pod.metadata.labels["run"]
  sigopt_conn = sigopt_settings.conn
  run = sigopt_conn.training_runs(run_id).fetch()
  run_context = RunContext(sigopt_conn, run)
  return RunState(run_context, sigopt_settings, k8s_settings, pod.metadata.name)

def set_events_on_sigterm(events):

  def handler(signum, frame):
    logging.error("sigterm received")
    for event in events:
      event.set()

  signal.signal(signal.SIGTERM, handler)

class RunPodsManager:
  def __init__(self, k8s_settings, run_name, run_id, sigopt_settings):
    self.k8s_settings = k8s_settings
    self.run_name = run_name
    self.run_id = run_id
    self.sigopt_settings = sigopt_settings
    self.run_states = dict()
    self.pod_modified_event = threading.Event()
    self.stop_event = threading.Event()
    self.watcher_thread = WatchPodsThread(
      k8s_settings=self.k8s_settings,
      label_selector=f"run-name={self.run_name},type=run",
      run_states=self.run_states,
      pods_modified_event=self.pod_modified_event,
      stop_threads_event=self.stop_event,
    )
    self.logger = logging.getLogger("controller:RunPodsManager")

  @classmethod
  def from_env(cls):
    s = RunSettings()
    return cls(
      k8s_settings=s.k8s_settings,
      run_name=s.run_name,
      run_id=s.run_id,
      sigopt_settings=s.sigopt_settings,
    )

  def start(self):
    sigterm_event = threading.Event()
    set_events_on_sigterm([sigterm_event, self.stop_event])
    try:
      pod = self.k8s_settings.api.read_namespaced_pod(self.run_name, self.k8s_settings.namespace)
      self.logger.info("found existing pod %s", self.run_name)
      run_state = create_run_state(self.sigopt_settings, pod, self.k8s_settings)
    except KubernetesApiException as kae:
      if kae.status != HTTPStatus.NOT_FOUND:
        raise
      sigopt_conn = self.sigopt_settings.conn
      run = sigopt_conn.training_runs(self.run_id).fetch()
      run_context = RunContext(sigopt_conn, run)
      run_state = RunState(run_context, self.sigopt_settings, self.k8s_settings, self.run_name)
      pod = create_run_pod(
        k8s_settings=self.k8s_settings,
        run_context=run_context,
      )
      self.logger.info("created pod %s", pod.metadata.name)
    self.run_states.update({self.run_name: run_state})
    self.watcher_thread.start()
    try:
      while not self.stop_event.is_set() and not run_state.is_finished():
        try:
          self.stop_event.wait(timeout=1)
        except TimeoutError:
          pass
    except KeyboardInterrupt:
      pass
    self.stop_event.set()
    self.watcher_thread.join()
    if self.watcher_thread.exception_occurred.is_set():
      raise Exception("An exception occurred in the watcher thread")
    if sigterm_event.is_set():
      raise Exception("Sigterm received")

class ExperimentPodsManager:
  def __init__(self, k8s_settings, sigopt_settings, experiment_id):
    self.k8s_settings = k8s_settings
    self.sigopt_settings = sigopt_settings
    self.experiment_id = experiment_id
    self.run_label_selector = f"experiment={self.experiment_id},type=run"
    self.run_state = dict()
    self.manage_pods_event = threading.Event()
    self.stop_threads_event = threading.Event()
    self.management_event_repeater = EventRepeater(5, self.manage_pods_event)
    self.refiller_thread = RefillExperimentPodsThread(
      self.k8s_settings,
      self.sigopt_settings,
      self.experiment_id,
      self.run_state,
      self.manage_pods_event,
      stop_threads_event=self.stop_threads_event,
    )
    self.watcher_thread = WatchPodsThread(
      self.k8s_settings,
      self.run_label_selector,
      self.run_state,
      self.manage_pods_event,
      stop_threads_event=self.stop_threads_event,
    )

  @classmethod
  def from_env(cls):
    s = ExperimentSettings()
    return cls(
      k8s_settings=s.k8s_settings,
      sigopt_settings=s.sigopt_settings,
      experiment_id=s.experiment_id,
    )

  def start(self):
    sigterm_event = threading.Event()
    set_events_on_sigterm([sigterm_event, self.stop_threads_event])
    self.run_state.update({
      pod.metadata.name: create_run_state(self.sigopt_settings, pod, self.k8s_settings)
      for pod in self.k8s_settings.api.list_namespaced_pod(
        self.k8s_settings.namespace,
        label_selector=self.run_label_selector,
      ).items
      if is_pod_active(pod)
    })
    self.manage_pods_event.set()
    threads = [self.refiller_thread, self.watcher_thread]
    for thread in threads:
      thread.start()
    self.management_event_repeater.start()
    try:
      while not self.stop_threads_event.is_set():
        try:
          self.stop_threads_event.wait(timeout=5)
        except TimeoutError:
          pass
    except KeyboardInterrupt:
      pass
    finally:
      self.management_event_repeater.cancel()
      self.stop_threads_event.set()
      self.manage_pods_event.set()
      for thread in threads:
        thread.join()
    if any(thread.exception_occurred.is_set() for thread in threads):
      raise Exception("An exception ocurred in at least 1 thread")
    if sigterm_event.is_set():
      raise Exception("Sigterm received")
