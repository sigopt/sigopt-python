from .defaults import get_default_name
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
