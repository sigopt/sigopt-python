import json

from sigopt.config import config
from sigopt.exception import ApiException
from sigopt.defaults import get_default_project
from sigopt.factory import SigOptFactory
from sigopt.interface import get_connection

from ..exceptions import CheckConnectionError
from ..services.base import Service


class SigOptService(Service):
  def __init__(self, services):
    super().__init__(services)
    self._conn = get_connection()

  @property
  def conn(self):
    return self._conn

  @property
  def api_token(self):
    return self.conn.impl.requestor.auth.username

  @property
  def api_url(self):
    return self.conn.impl.api_url

  @property
  def verify_ssl_certs(self):
    return self.conn.impl.requestor.verify_ssl_certs

  def log_collection_enabled(self):
    return config.log_collection_enabled

  def check_connection(self):
    try:
      self.conn.experiments().fetch(limit=1)
    except ApiException as e:
      raise CheckConnectionError(f'An error occured while checking your SigOpt connection: {e}') from e

  def create_experiment(self, experiment_body, project_id):
    factory = SigOptFactory(project_id)
    return factory.create_prevalidated_experiment(experiment_body)

  def fetch_experiment(self, experiment_id):
    factory = SigOptFactory.from_default_project()
    return factory.get_experiment(experiment_id)

  def create_run(self, run_name, cluster, project_id):
    factory = SigOptFactory(project_id)
    return factory.create_run(
      name=run_name,
      metadata={'cluster_name': cluster.name},
    )

  def fetch_run(self, run_id):
    return self.conn.training_runs(run_id).fetch()

  def ensure_project_exists(self, project_id):
    factory = SigOptFactory(project_id)
    return factory.ensure_project_exists()

  def iterate_runs_by_filters(self, filters, project=None, client=None):
    if project is None:
      client, project = SigOptFactory.from_default_project().ensure_project_exists()
    return (
      self.conn.clients(client)
        .projects(project)
        .training_runs()
        .fetch(filters=json.dumps(filters))
        .iterate_pages()
    )

  def iterate_runs(self, experiment):
    if experiment.project:
      return self.iterate_runs_by_filters(
        [{'operator': '==', 'field': 'experiment', 'value': experiment.id}],
        project=experiment.project,
        client=experiment.client,
      )
    # TODO(patrick): api.sigopt.com returns extended JSON for the new endpoint fetch, which we need for the state
    # field. But we can only do that for experiments in projects.
    # So we fall back safely here, but this can be removed in the future
    return self.conn.experiments(experiment.id).training_runs().fetch().iterate_pages()

  def safe_fetch_experiment(self, experiment_id):
    try:
      return self.fetch_experiment(experiment_id)
    except ApiException as e:
      if e.status_code in [403, 404]:
        return None
      raise
