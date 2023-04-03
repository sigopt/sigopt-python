# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
IDENTIFIER_TYPE_EXPERIMENT = "experiment"
IDENTIFIER_TYPE_RUN = "run"
IDENTIFIER_TYPE_SUGGESTION = "suggestion"
VALID_IDENTIFIER_TYPES = {
  IDENTIFIER_TYPE_EXPERIMENT,
  IDENTIFIER_TYPE_RUN,
  IDENTIFIER_TYPE_SUGGESTION,
}
IDENTIFIER_QUERY_ID = "id"
IDENTIFIER_QUERY_NAME = "name"
IDENTIFIER_QUERY_SUGGESTION = "suggestion"


def parse_identifier(id_str):
  if "/" not in id_str:
    return {
      "raw": id_str,
      "type": IDENTIFIER_TYPE_RUN,
      "query": IDENTIFIER_QUERY_NAME,
      "value": id_str,
      "pod_label_selector": f"type=run,run-name={id_str}",
      "controller_label_selector": f"type=controller,run-name={id_str}",
    }
  _type, _id = id_str.split("/", 1)
  if _type not in VALID_IDENTIFIER_TYPES:
    raise ValueError(f"Invalid type: {_type}")
  if not _id.isdigit():
    raise ValueError(f"Invalid id: {_id}")
  return {
    "raw": id_str,
    "type": _type,
    "query": IDENTIFIER_QUERY_ID,
    "value": _id,
    "pod_label_selector": f"type=run,{_type}={_id}",
    "controller_label_selector": f"type=controller,{_type}={_id}",
  }


def maybe_convert_to_run_identifier(identifier):
  if identifier["type"] == IDENTIFIER_TYPE_SUGGESTION:
    return {
      "raw": identifier["raw"],
      "type": IDENTIFIER_TYPE_RUN,
      "query": IDENTIFIER_QUERY_SUGGESTION,
      "value": identifier["value"],
      "pod_label_selector": identifier["pod_label_selector"],
      "controller_label_selector": identifier["controller_label_selector"],
    }
  return identifier


def get_run_and_pod_from_identifier(identifier, services):
  identifier = maybe_convert_to_run_identifier(identifier)
  assert identifier["type"] == IDENTIFIER_TYPE_RUN, f"Can't get a single run or pod from {identifier['raw']}"
  run = None
  run_id = None
  pod = None

  # find the run from the identifier
  if identifier["query"] in (IDENTIFIER_QUERY_NAME, IDENTIFIER_QUERY_SUGGESTION):
    filter_field = identifier["query"]
    filter_value = identifier["value"]
    runs = list(
      services.sigopt_service.iterate_runs_by_filters(
        [{"operator": "==", "field": filter_field, "value": filter_value}],
      )
    )
    if len(runs) > 1:
      raise Exception(f"Multiple runs found with {filter_field}: {filter_value}")
    if len(runs) == 1:
      run = runs[0]
  elif identifier["query"] == IDENTIFIER_QUERY_ID:
    run_id = identifier["value"]
    run = services.sigopt_service.conn.training_runs(run_id).fetch()
  else:
    raise NotImplementedError(identifier["query"])

  pods = services.kubernetes_service.get_pods_by_label_selector(identifier["pod_label_selector"]).items
  assert len(pods) < 2, f"Multiple pods found for {identifier['raw']}"
  if len(pods) == 1:
    pod = pods[0]

  return run, pod
