# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from ..services.base import Service


class JobStatusService(Service):
  def parse_job(self, job):
    job_name = job.metadata.name

    conditions = []
    if job.status.conditions:
      for c in job.status.conditions:
        if c.status == "True":
          conditions.append(c.type)
        elif c.status == "False":
          conditions.append(f"Not {c.type}")
        else:
          conditions.append(f"Maybe {c.type}")

    job_status = ", ".join(conditions) if conditions else "Not Complete"

    experiment_id = self.services.job_runner_service.experiment_id(job_name)
    experiment = self.services.sigopt_service.safe_fetch_experiment(experiment_id)

    return dict(
      experiment=experiment,
      name=job_name,
      status=job_status,
      experiment_id=experiment_id or "??",
      experiment_name=(experiment.name if experiment else "unknown"),
      budget=(str(float(experiment.budget)) if experiment and experiment.budget is not None else "n/a"),
      total_run_count=str(experiment.progress.total_run_count) if experiment else "n/a",
    )

  def get_runs_by_pod(self, experiment):
    runs_by_pod = dict()
    for run in self.services.sigopt_service.iterate_runs(experiment):
      pod_name = run.metadata.get("pod_name") if run.metadata else "UNKNOWN"

      if pod_name not in runs_by_pod:
        runs_by_pod[pod_name] = dict(success=0, failed=0)

      # TODO(patrick): Include active state in output as well
      if run.state == "failed":
        runs_by_pod[pod_name]["failed"] += 1
      elif run.state != "active":
        runs_by_pod[pod_name]["success"] += 1

    return runs_by_pod

  def parse_pod(self, pod, runs_by_pod):
    pod_name = pod.metadata.name
    runs = runs_by_pod.get(pod_name, dict(success=0, failed=0))

    phase = pod.status.phase
    status = phase
    if phase in ["Pending", "Failed", "Unknown"]:
      reasons = [condition.reason for condition in pod.status.conditions if condition.reason]
      if reasons:
        status = f'{status} - {", ".join(reasons)}'

    return dict(
      name=pod_name,
      success=runs["success"],
      failed=runs["failed"],
      status=status,
    )
