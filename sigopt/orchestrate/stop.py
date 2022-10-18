# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from .identifier import IDENTIFIER_TYPE_EXPERIMENT, IDENTIFIER_TYPE_RUN, get_run_and_pod_from_identifier


def stop_experiment(experiment_identifier, services):
  assert experiment_identifier["type"] == IDENTIFIER_TYPE_EXPERIMENT
  experiment_jobs = services.kubernetes_service.get_jobs_by_label_selector(
    experiment_identifier["controller_label_selector"],
  ).items

  for job in experiment_jobs:
    services.kubernetes_service.delete_job(job.metadata.name, propogation_policy='Background')

def stop_run(run_identifier, services):
  assert run_identifier["type"] == IDENTIFIER_TYPE_RUN

  _, pod = get_run_and_pod_from_identifier(run_identifier, services)

  if pod:
    services.kubernetes_service.delete_pod(pod.metadata.name)

  run_controller_jobs = services.kubernetes_service.get_jobs_by_label_selector(
    run_identifier["controller_label_selector"],
  ).items
  for job in run_controller_jobs:
    services.kubernetes_service.delete_job(job.metadata.name, propogation_policy='Background')
