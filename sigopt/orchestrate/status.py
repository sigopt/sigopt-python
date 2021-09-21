from .identifier import (
  IDENTIFIER_QUERY_ID,
  IDENTIFIER_QUERY_NAME,
  IDENTIFIER_QUERY_SUGGESTION,
  IDENTIFIER_TYPE_EXPERIMENT,
  IDENTIFIER_TYPE_RUN,
  IDENTIFIER_TYPE_SUGGESTION,
  get_run_and_pod_from_identifier,
  maybe_convert_to_run_identifier,
)


def print_experiment_status(experiment_identifier, services):
  assert experiment_identifier["type"] == IDENTIFIER_TYPE_EXPERIMENT
  assert experiment_identifier["query"] == IDENTIFIER_QUERY_ID
  experiment_id = experiment_identifier["value"]
  experiment = services.sigopt_service.fetch_experiment(experiment_id)

  parsed_job = {}
  parsed_job["experiment_id"] = experiment_id
  parsed_job["experiment_name"] = experiment.name
  parsed_job["budget"] = (
    str(float(experiment.budget))
    if experiment and experiment.budget is not None
    else 'n/a'
  )
  parsed_job["total_run_count"] = (
    str(experiment.progress.total_run_count) if experiment else 'n/a'
  )

  runs = list(services.sigopt_service.iterate_runs(experiment))
  total_failures = sum(v.state == 'failed' for v in runs)

  yield 'Experiment Name: {experiment_name}'.format(**parsed_job)
  yield '{total_run_count} / {budget} budget'.format(
    **parsed_job
  )
  yield f'{total_failures} Run(s) failed'

  yield '{:20}\t{:15}\t{:15}\t{:35}'.format(
    "Run Name",
    "Pod phase",
    "Status",
    "Link",
  )

  pods_by_name = {
    pod.metadata.name: pod
    for pod in services.kubernetes_service.get_pods_by_label_selector(
      experiment_identifier["pod_label_selector"],
    ).items
  }
  runs_by_name = {run.to_json()["name"]: run for run in runs}
  for run_name in sorted(set(pods_by_name) | set(runs_by_name)):
    run = runs_by_name.get(run_name)
    pod = pods_by_name.get(run_name)
    state = run.state if run else 'creating'
    phase = pod.status.phase if pod else 'Deleted'
    url = f"https://app.sigopt.com/run/{run.id}" if run else ""
    yield f'{run_name:20}\t{phase:15}\t{state:15}\t{url:35}'

  yield (
    "Follow logs: "
    f"sigopt cluster kubectl logs -ltype=run,experiment={experiment.id} --max-log-requests=1000 -f"
  )
  yield f'View more at: https://app.sigopt.com/experiment/{experiment_id}'

def print_run_status(run_identifier, services):
  run_identifier = maybe_convert_to_run_identifier(run_identifier)
  run, pod = get_run_and_pod_from_identifier(run_identifier, services)
  if not run and not pod:
    yield f"Could not find a run for {run_identifier['raw']}"
    return

  run_id = None
  run_name = None
  run_state = None
  pod_phase = None
  node_name = None
  suggestion_id = None
  observation_id = None
  experiment_id = None

  # scrape info from identifier
  if run_identifier["query"] == IDENTIFIER_QUERY_NAME:
    run_name = run_identifier["value"]
  elif run_identifier["query"] == IDENTIFIER_QUERY_SUGGESTION:
    suggestion_id = run_identifier["value"]

  # scrape info from the run
  if run:
    run_data = run.to_json()
    run_id = run.id
    run_name = run_name or run_data["name"]
    run_state = run_state or run.state
    suggestion_id = suggestion_id or run_data.get("suggestion")
    observation_id = observation_id or run_data.get("observation")
    experiment_id = experiment_id or run_data.get("experiment")

  # scrape info from the pod
  if pod:
    run_name = run_name or pod.metadata.name
    node_name = node_name or pod.spec.node_name
    pod_phase = pod_phase or pod.status.phase

  # set values if still None
  run_state = run_state or 'creating'
  pod_phase = pod_phase or 'Deleted'
  node_name = node_name or 'unknown'

  yield f"Run Name: {run_name}"
  if run_id is not None:
    yield f"Link: https://app.sigopt.com/run/{run_id}"
  yield f"State: {run_state}"
  if experiment_id is not None:
    yield f"Experiment link: https://app.sigopt.com/experiment/{experiment_id}"
  if suggestion_id is not None:
    yield f"Suggestion id: {suggestion_id}"
  if observation_id is not None:
    yield f"Observation id: {observation_id}"
  yield f"Pod phase: {pod_phase}"
  yield f"Node name: {node_name}"
  yield (
    "Follow logs: "
    f"sigopt cluster kubectl logs \"pod/{run_name}\" -f"
  )

IDENTIFIER_TYPE_TO_PRINTER = {
  IDENTIFIER_TYPE_EXPERIMENT: print_experiment_status,
  IDENTIFIER_TYPE_RUN: print_run_status,
  IDENTIFIER_TYPE_SUGGESTION: print_run_status,
}

def print_status(identifier, services):
  try:
    printer = IDENTIFIER_TYPE_TO_PRINTER[identifier["type"]]
  except KeyError as ke:
    raise NotImplementedError() from ke
  return printer(identifier, services)
