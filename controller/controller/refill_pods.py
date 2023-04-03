# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from controller.create_pod import create_run_pod, random_run_name
from controller.missing_pods import get_missing_experiment_pod_count
from controller.run_state import RunState
from controller.thread import ControllerThread

from sigopt.factory import SigOptFactory


def count_active_runs(run_states):
  return sum(1 for run_state in run_states.values() if run_state.is_active())


class RefillExperimentPodsThread(ControllerThread):
  def __init__(self, *args, stop_threads_event, **kwargs):
    super().__init__(
      target=self.refill_experiment_pods,
      stop_threads_event=stop_threads_event,
      args=args,
      kwargs=kwargs,
    )

  def refill_experiment_pods(
    self,
    k8s_settings,
    sigopt_settings,
    experiment_id,
    run_states,
    refill_pods_event,
  ):
    logger = self.logger
    logger.info("starting management loop")
    project = sigopt_settings.project
    run_factory = SigOptFactory(project, connection=sigopt_settings.conn).get_aiexperiment(experiment_id)
    while True:
      refill_pods_event.wait()
      refill_pods_event.clear()
      if self.stop_threads_event.is_set():
        break
      logger.debug("checking pod count")
      active_run_count = count_active_runs(run_states)
      logger.debug("active run count %s", active_run_count)
      missing_pod_count = get_missing_experiment_pod_count(sigopt_settings.conn, active_run_count, experiment_id)
      logger.debug("missing pod count %s", missing_pod_count)
      if missing_pod_count + active_run_count == 0:
        logger.info("no more pods to add and no runs are active")
        break
      if missing_pod_count:
        logger.info("adding %s pods", missing_pod_count)
      for _ in range(missing_pod_count):
        run_name = random_run_name()
        logger.debug("creating run %s", run_name)
        run_context = run_factory.create_run(name=run_name)
        run_context.log_metadata("cluster_name", k8s_settings.cluster_name)
        run_states[run_name] = RunState(run_context, sigopt_settings, k8s_settings, run_name)
        pod = create_run_pod(
          k8s_settings=k8s_settings,
          run_context=run_context,
        )
        logger.info("added pod %s", pod.metadata.name)
    logger.info("exited refill loop")
