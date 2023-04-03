# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import collections
import logging

from controller.k8s_constants import K8sPhase
from controller.pod_status import is_pod_phase_active, is_pod_phase_finished

from sigopt.exception import ApiException
from sigopt.run_context import RunContext


PodState = collections.namedtuple(
  "PodState",
  [
    "phase",
    "termination_info",
  ],
)


def get_relevant_state_from_pod_event(event):
  pod = event["object"]
  phase = pod.status.phase
  termination_info = None
  container_statuses = pod.status.container_statuses
  if container_statuses:
    container_terminated = container_statuses[0].state.terminated
    if container_terminated:
      termination_info = (container_terminated.reason, container_terminated.exit_code)
  return PodState(
    phase=phase,
    termination_info=termination_info,
  )


# NOTE(taylor): this class maintains a local state of the run pod
# and updates the SigOpt API when there are changes
class RunState:
  @classmethod
  def create_from_pod(cls, sigopt_settings, k8s_settings, pod):
    run_id = pod.metadata.labels["run"]
    sigopt_conn = sigopt_settings.conn
    run = sigopt_conn.training_runs(run_id).fetch()
    run_context = RunContext(sigopt_conn, run)
    return cls(run_context, sigopt_settings, k8s_settings, pod.metadata.name)

  def __init__(self, run_context, sigopt_settings, k8s_settings, pod_name):
    self.state = None
    self.run_context = run_context
    self.sigopt_settings = sigopt_settings
    self.k8s_settings = k8s_settings
    self.pod_name = pod_name
    self.logger = logging.getLogger("controller:RunState")

  def get_phase(self):
    phase = K8sPhase.PENDING
    if self.state:
      phase = self.state.phase
    return phase

  def is_active(self):
    return is_pod_phase_active(self.get_phase())

  def is_finished(self):
    return is_pod_phase_finished(self.get_phase())

  def process_pod_event(self, event):
    new_state = get_relevant_state_from_pod_event(event)
    self.update_state(new_state)

  def update_state(self, new_state):
    self.maybe_update_termination_info(new_state.termination_info)
    self.maybe_update_phase(new_state.phase)
    self.state = new_state

  def update_run_logs(self):
    if self.sigopt_settings.log_collection_enabled:
      logs = self.k8s_settings.api.read_namespaced_pod_log(self.pod_name, self.k8s_settings.namespace)
      self.run_context.set_logs({"all": logs})

  def maybe_update_phase(self, new_phase):
    if not self.state or new_phase != self.state.phase:
      self.run_context.log_metadata("pod_phase", new_phase)
      if is_pod_phase_finished(new_phase):
        self.update_run_logs()
        try:
          self.run_context.end(exception=None if new_phase == K8sPhase.SUCCEEDED else "PodFailed")
        except ApiException:
          pass

  def maybe_update_termination_info(self, new_termination_info):
    if not self.state or new_termination_info != self.state.termination_info:
      if new_termination_info:
        termination_reason, exit_code = new_termination_info
        self.run_context.log_metadata("termination_reason", termination_reason)
        self.run_context.log_metadata("exit_code", exit_code)
