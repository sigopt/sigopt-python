def get_missing_experiment_pod_count(conn, current_pod_count, experiment_id):
  e = conn.experiments(experiment_id).fetch()
  expected_num_pods = e.parallel_bandwidth or 1
  if e.budget is not None:
    expected_num_pods = min(expected_num_pods, e.budget - e.progress.budget_consumed)
  return int(max(expected_num_pods - current_pod_count, 0))
