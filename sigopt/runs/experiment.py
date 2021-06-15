from .context import LiveRunContext


class ExperimentContext(object):
  def __init__(self, connection, experiment):
    self._connection = connection
    self._experiment = experiment

  def create_run(self, name=None):
    return LiveRunContext.create_from_experiment(
      connection=self._connection,
      run_name=name,
      experiment=self._experiment,
    )

  def refresh(self):
    self._experiment = self._connection.experiments(self._experiment.id).fetch()

  def is_finished(self):
    self.refresh()
    if self._experiment.observation_budget is None:
      return False
    return self._experiment.progress.observation_budget_consumed >= self._experiment.observation_budget

  def loop(self):
    while not self.is_finished():
      yield self.create_run()
