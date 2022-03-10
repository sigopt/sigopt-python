from sigopt.validate import validate_experiment_input

from .defaults import check_valid_project_id, ensure_project_exists, get_default_project
from .interface import get_connection
from .sigopt_logging import print_logger
from .run_factory import BaseRunFactory
from .experiment_context import ExperimentContext
from .validate.keys import PROJECT_KEY, RUNS_ONLY_KEY
from .run_context import global_run_context
from .utils import batcher


class SigOptFactory(BaseRunFactory):
  '''A SigOptFactory creates Runs and Experiments that belong to a specified Project.'''

  _project_id = None
  _assume_project_exists = False
  _client_id = None

  @classmethod
  def from_default_project(cls):
    project_id = get_default_project()
    return cls(project_id)

  def __init__(self, project_id, connection=None):
    self.set_project(project_id)
    self._connection = connection

  def set_project(self, project):
    check_valid_project_id(project)
    self._project_id = project
    self._assume_project_exists = False
    self._client_id = None

  @property
  def connection(self):
    if self._connection is None:
      self._connection = get_connection()
    return self._connection

  @property
  def project(self):
    return self._project_id

  def _on_experiment_created(self, experiment):
    print_logger.info(
      "Experiment created, view it on the SigOpt dashboard at https://app.sigopt.com/experiment/%s",
      experiment.id,
    )

  def ensure_project_exists(self):
    # if we have already ensured that the project exists then we can skip this step in the future
    if not self._assume_project_exists:
      self._client_id = ensure_project_exists(self.connection, self.project)
      self._assume_project_exists = True
    return self._client_id, self.project

  def _create_run(self, name, metadata):
    connection = self.connection
    client_id, project_id = self.ensure_project_exists()
    run = connection.clients(client_id).projects(project_id).training_runs().create(name=name, metadata=metadata)
    run_context = self.run_context_class(connection, run, global_run_context.params)
    return run_context

  def upload_runs(self, runs, max_batch_size=10000):
    connection = self.connection
    client_id, project_id = self.ensure_project_exists()
    result = []
    for batch in batcher(runs, max_batch_size):
      result.extend(
        connection.clients(client_id).projects(project_id).training_runs().create_batch(runs=batch, fields='id').data
      )
    return result

  def create_prevalidated_experiment(self, validated_body):
    connection = self.connection
    client_id, project_id = self.ensure_project_exists()
    experiment = connection.clients(client_id).experiments().create(
      **{PROJECT_KEY: project_id, RUNS_ONLY_KEY: True},
      **validated_body,
    )
    self._on_experiment_created(experiment)
    return ExperimentContext(experiment, connection=connection)

  def create_experiment(self, *, name, parameters, metrics, **experiment_body):
    # name, parameters and metrics are always required and placing them in the signature
    # results in more pythonic errors
    experiment_body["name"] = name
    experiment_body["parameters"] = parameters
    experiment_body["metrics"] = metrics
    validated = validate_experiment_input(experiment_body)
    return self.create_prevalidated_experiment(validated)

  def get_experiment(self, experiment_id):
    connection = self.connection
    experiment = connection.experiments(experiment_id).fetch()
    if experiment.project is None:
      raise ValueError(
        f"The requested experiment {experiment_id} does not belong to a project."
        " Only experiments in projects are compatible with this client."
      )
    if experiment.project != self._project_id:
      print_logger.warning(
        "Warning: experiment %s does not belong to the configured project %s",
        experiment_id,
        self._project_id,
      )
    return ExperimentContext(experiment, connection=connection)

  def archive_experiment(self, experiment_id):
    self.connection.experiments(experiment_id).delete()

  def unarchive_experiment(self, experiment_id):
    self.connection.experiments(experiment_id).update(state="active")

  def archive_run(self, run_id):
    self.connection.training_runs(run_id).delete()

  def unarchive_run(self, run_id):
    self.connection.training_runs(run_id).update(deleted=False)

  def get_run(self, run_id):
    return self.connection.training_runs(run_id).fetch()
