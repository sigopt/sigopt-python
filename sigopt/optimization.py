import warnings


def optimization_loop(connection, experiment, loop_body):
  while (
    experiment.observation_budget is None or
    experiment.progress.observation_budget_consumed < experiment.observation_budget
  ):
    suggestion = connection.experiments(experiment.id).suggestions().create()
    try:
      loop_body(suggestion)
    except KeyboardInterrupt:
      break
    except Exception as e:
      warnings.warn(
        'Exception caught: {}'.format(str(e)),
        RuntimeWarning,
      )
    experiment = connection.experiments(experiment.id).fetch()
  return experiment
