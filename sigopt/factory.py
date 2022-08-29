import http

import click

from sigopt.validate import validate_aiexperiment_input

from .defaults import check_valid_project_id, ensure_project_exists, get_default_project, get_client_id
from .interface import get_connection
from .sigopt_logging import print_logger
from .run_factory import BaseRunFactory
from .exception import ProjectNotFoundException
from .aiexperiment_context import AIExperimentContext
from .run_context import global_run_context
from .utils import batcher
from .exception import ApiException, ConflictingProjectException


class SigOptFactory(BaseRunFactory):
  '''A SigOptFactory creates Runs and AIExperiments that belong to a specified Project.'''

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

  def _on_aiexperiment_created(self, aiexperiment):
    print_logger.info(
      "AIExperiment created, view it on the SigOpt dashboard at https://app.sigopt.com/experiment/%s",
      aiexperiment.id,
    )

  def create_project(self, id_=None, name=None):
    if id_ is not None:
      self.set_project(id_)
    if name is None:
      name = self.project
    client_id = get_client_id(self.connection)
    try:
      project = self.connection.clients(client_id).projects().create(id=self.project, name=name)
    except ApiException as e:
      if e.status_code == http.HTTPStatus.CONFLICT:
        raise ConflictingProjectException(self.project) from e
      raise
    self._client_id = client_id
    self._assume_project_exists = True
    return project

  def set_up_cli(self):
    try:
      self.ensure_project_exists()
    except ProjectNotFoundException as pnfe:
      raise click.ClickException(pnfe) from pnfe

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

  def create_prevalidated_aiexperiment(self, validated_body):
    connection = self.connection
    client_id, project_id = self.ensure_project_exists()
    aiexperiment = connection.clients(client_id).projects(project_id).aiexperiments().create(
      **validated_body,
    )
    self._on_aiexperiment_created(aiexperiment)
    return AIExperimentContext(aiexperiment, connection=connection)

  def create_experiment(self, *args, **kwargs):
    return self.create_aiexperiment(*args, **kwargs)

  def create_aiexperiment(self, *, name, parameters, metrics, **aiexperiment_body):
    # name, parameters and metrics are always required and placing them in the signature
    # results in more pythonic errors
    aiexperiment_body["name"] = name
    aiexperiment_body["parameters"] = parameters
    aiexperiment_body["metrics"] = metrics
    validated = validate_aiexperiment_input(aiexperiment_body)
    return self.create_prevalidated_aiexperiment(validated)

  def get_experiment(self, experiment_id):
    return self.get_aiexperiment(experiment_id)

  def get_aiexperiment(self, aiexperiment_id):
    connection = self.connection
    aiexperiment = connection.aiexperiments(aiexperiment_id).fetch()
    if aiexperiment.project != self._project_id:
      print_logger.warning(
        "Warning: AIExperiment %s does not belong to the configured project %s",
        aiexperiment_id,
        self._project_id,
      )
    return AIExperimentContext(aiexperiment, connection=connection)

  def archive_experiment(self, experiment_id, *args, **kwargs):
    return self.archive_aiexperiment(experiment_id, *args, **kwargs)

  def archive_aiexperiment(self, aiexperiment_id, include_runs=False):
    self.connection.aiexperiments(aiexperiment_id).delete(include_runs="true" if include_runs else "false")

  def unarchive_experiment(self, experiment_id):
    self.unarchive_aiexperiment(experiment_id)

  def unarchive_aiexperiment(self, aiexperiment_id):
    self.connection.aiexperiments(aiexperiment_id).update(state="active")

  def archive_run(self, run_id):
    self.connection.training_runs(run_id).delete()

  def unarchive_run(self, run_id):
    self.connection.training_runs(run_id).update(deleted=False)

  def get_run(self, run_id):
    return self.connection.training_runs(run_id).fetch()
