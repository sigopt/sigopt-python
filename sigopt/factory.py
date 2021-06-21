from .defaults import check_valid_project_id, ensure_project_exists
from .interface import get_connection
from .run_factory import BaseRunFactory
from .experiment_context import ExperimentContext


class SigOptFactory(BaseRunFactory):
  '''A SigOptFactory creates Runs and Experiments that belong to a specified Project.'''

  def __init__(self, project_id):
    check_valid_project_id(project_id)
    self._project_id = project_id
    self._assume_project_exists = False
    self._client_id = None

  @property
  def project(self):
    return self._project_id

  def _ensure_project_exists(self):
    # if we have already ensured that the project exists then we can skip this step in the future
    if not self._assume_project_exists:
      self._client_id = ensure_project_exists(get_connection(), self.project)
      self._assume_project_exists = True
    return self._client_id, self.project

  def _create_run(self, name):
    connection = get_connection()
    client_id, project_id = self._ensure_project_exists()
    run = connection.clients(client_id).projects(project_id).training_runs().create(name=name)
    run_context = self.run_context_class(connection, run, suggestion=None)
    print(
      'Run started, view it on the SigOpt dashboard at https://app.sigopt.com/run/{run_id}'.format(
        run_id=run.id,
      )
    )
    return run_context

  def create_experiment(self, name, parameters, metrics=None, budget=None, **kwargs):
    connection = get_connection()
    client_id, project_id = self._ensure_project_exists()
    experiment = connection.clients(client_id).experiments().create(
      name=name,
      metrics=metrics,
      parameters=parameters,
      project=project_id,
      observation_budget=budget,
      **kwargs,
    )
    return ExperimentContext(experiment)
