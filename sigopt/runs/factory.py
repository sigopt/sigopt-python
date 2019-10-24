import contextlib

from ..exception import RunException
from ..interface import Connection
from .context import LiveRunContext, NullRunContext


class RunFactory(object):
  CONFIG_CONTEXT_KEY = 'run_connection'
  RUN_CONTEXT_KEY = 'run_context'

  _global_run_context = None
  _global_connection = None
  _null_run_context = NullRunContext()

  @classmethod
  def get_global_run_context(cls):
    if cls._global_run_context:
      return cls._global_run_context
    return cls._null_run_context

  @classmethod
  def from_config(cls, config):
    data = config.get_context_data(cls) or {}
    run_factory = cls()
    run_context_data = data.get(cls.RUN_CONTEXT_KEY)
    if run_context_data:
      cls._push_global_run(LiveRunContext.from_json(
        run_factory.connection,
        run_context_data,
      ))
    config.set_context_entry(run_factory)
    return run_factory

  @classmethod
  def _push_global_run(cls, run_context):
    if cls._global_run_context is None:
      cls._global_run_context = run_context
    else:
      raise RunException('A global run already exists')

  @classmethod
  def _pop_global_run(cls):
    if cls._global_run_context is None:
      raise RunException('No global run exists')
    global_run = cls._global_run_context
    cls._global_run_context = None
    return global_run

  @classmethod
  def _get_connection_singleton(cls):
    if cls._global_connection is None:
      cls._global_connection = Connection()
    return cls._global_connection

  def __init__(self):
    self._all_assignments = {}

  @property
  def connection(self):
    return self._get_connection_singleton()

  def to_json(self):
    run_context_data = self._global_run_context and self._global_run_context.to_json()
    return {
      self.RUN_CONTEXT_KEY: run_context_data,
    }

  @contextlib.contextmanager
  def create_global_run(self, name=None, project=None, suggestion=None):
    with self.create_run(name=name, project=project, suggestion=suggestion) as run:
      self._push_global_run(run)
      try:
        yield run
      finally:
        self._pop_global_run()

  def create_run(self, name=None, project=None, suggestion=None):
    return LiveRunContext.create(
      self.connection,
      run_name=name,
      project_id=project,
      suggestion=suggestion,
      all_assignments=self._all_assignments,
    )
