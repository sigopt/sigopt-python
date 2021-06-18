import threading

from .interface import get_connection
from .run_factory import BaseRunFactory
from .defaults import assert_valid_project_id, get_default_project, ensure_project_exists


class ExperimentContext(BaseRunFactory):
  '''Inherits the create_run method from BaseRunFactory.'''

  def __init__(self, experiment):
    assert experiment.project, "The experiment must belong to a project"
    self._experiment = experiment
    self._refresh_lock = threading.Lock()

  def refresh(self):
    '''Refresh the state of the Experiment from the SigOpt API.'''
    connection = get_connection()
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

  def _create_run(self, name):
    experiment = self._experiment
    client_id, project_id = experiment.client, experiment.project
    connection = get_connection()
    suggestion = connection.experiments(experiment.id).suggestions().create()
    run = connection.clients(client_id).projects(project_id).training_runs().create(
      name=name,
      suggestion=suggestion.id,
    )
    run_context = self.run_context_class(connection, run, suggestion)
    print(
      'Run started, view it on the SigOpt dashboard at https://app.sigopt.com/run/{run_id}'.format(
        run_id=run.id,
      )
    )
    return run_context

def create_experiment(name, parameters, metrics=None, project=None, budget=None, **kwargs):
    if project is None:
      project = get_default_project()
    else:
      assert_valid_project_id(project)
    connection = get_connection()
    ensure_project_exists(connection, project)
    experiment = connection.experiments().create(
      name=name,
      metrics=metrics,
      parameters=parameters,
      project=project,
      observation_budget=budget,
      **kwargs,
    )
    return ExperimentContext(experiment)
