import threading

from .run_factory import BaseRunFactory


class ExperimentContext(BaseRunFactory):
  '''Wraps the Experiment object and provides extra utility methods.'''

  def __init__(self, experiment, connection):
    if experiment.project is None:
      raise ValueError("experiment does not belong to a project")
    self._experiment = experiment
    self._refresh_lock = threading.Lock()
    self._connection = connection

  def refresh(self):
    '''Refresh the state of the Experiment from the SigOpt API.'''
    connection = self._connection
    with self._refresh_lock:
      self._experiment = connection.experiments(self.id).fetch()

  def is_finished(self):
    '''Check if the experiment has consumed its entire budget.'''
    self.refresh()
    if self.budget is None:
      return False
    return self.budget_consumed >= self.budget

  def loop(self, name=None):
    '''Create runs until the experiment has finished.'''
    while not self.is_finished():
      yield self.create_run(name=name)

  def archive(self):
    connection = self._connection
    connection.experiments(self.id).delete()
    self.refresh()

  @property
  def budget(self):
    return self.observation_budget

  @property
  def budget_consumed(self):
    return self.progress.observation_budget_consumed

  @property
  def project(self):
    # delegate to __getattr__
    raise AttributeError

  def __getattr__(self, attr):
    return getattr(self._experiment, attr)

  def _create_run(self, name, metadata):
    experiment = self._experiment
    connection = self._connection
    run = connection.experiments(experiment.id).training_runs().create(
      name=name,
      metadata=metadata,
    )
    run_context = self.run_context_class(connection, run)
    return run_context
