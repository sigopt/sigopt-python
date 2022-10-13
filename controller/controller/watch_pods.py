# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from kubernetes import watch

from controller.thread import ControllerThread
from controller.pod_status import is_pod_finished
from controller.k8s_constants import K8sEvent

class WatchPodsThread(ControllerThread):
  def __init__(self, *args, stop_threads_event, **kwargs):
    super().__init__(target=self.watch_pods, stop_threads_event=stop_threads_event, args=args, kwargs=kwargs)

  def watch_pods(self, k8s_settings, label_selector, run_states, pods_modified_event):
    logger = self.logger
    logger.info("starting pod watcher loop")
    watcher = watch.Watch()
    while not self.stop_threads_event.is_set():
      logger.debug("restarting watch stream")
      for event in watcher.stream(
        k8s_settings.api.list_namespaced_pod,
        k8s_settings.namespace,
        label_selector=label_selector,
        timeout_seconds=5,
      ):
        if self.stop_threads_event.is_set():
          break
        pod = event["object"]
        pod_name = pod.metadata.name
        event_type = event["type"]
        logger.debug("event %s, pod %s", event_type, pod_name)
        try:
          run_state = run_states[pod_name]
        except KeyError:
          logger.error("event %s received for unknown pod %s", event_type, pod_name)
          continue
        run_state.process_pod_event(event)
        if event_type == K8sEvent.DELETED or is_pod_finished(pod):
          del run_states[pod_name]
          logger.info("pod removed %s", pod_name)
          pods_modified_event.set()
    logger.info("exited pod watcher loop")
