from .defaults import assert_valid_project_id, ensure_project_exists, get_default_name
from .interface import get_connection
from .run_context import RunContext


class BaseRunFactory(object):
  run_context_class = RunContext

  @property
  def project(self):
    raise NotImplementedError

  def _create_run(self, name):
    raise NotImplementedError

  def create_run(self, name=None):
    if name is None:
      name = get_default_name(self.project)
    return self._create_run(name)

  def create_global_run(self, global_run_context, *args, **kwargs):
    global_run_context.set_global_run(lambda: self.create_run(*args, **kwargs))

class RunFactory(BaseRunFactory):
  def __init__(self, project_id):
    assert_valid_project_id(project_id)
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
