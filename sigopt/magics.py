import sys
import yaml
import IPython
from IPython.core.magic import (
  Magics,
  cell_magic,
  magics_class,
)

from .cli.validate import PROJECT_KEY
from .config import config
from .interface import Connection
from .log_capture import NullStreamMonitor, SystemOutputStreamMonitor
from .optimization import optimization_loop
from .runs import create_global_run
from .runs.defaults import ensure_project_exists, get_default_project
from .vendored import six
from .lib import get_app_url

def get_ns():
  # NOTE(taylor): inspired by https://github.com/ipython/ipython/blob/master/IPython/core/interactiveshell.py
  # Walk up the stack trace until we find the 'exit' command
  stack_depth = 1
  while True:
    frame = sys._getframe(stack_depth)
    locals = frame.f_locals
    try:
      if isinstance(locals['exit'], IPython.core.autocall.ExitAutocall):
        return locals
    except KeyError:
      pass
    stack_depth += 1

@magics_class
class SigOptMagics(Magics):
  def __init__(self, shell):
    super(SigOptMagics, self).__init__(shell)
    self._connection = Connection()
    self._experiment = None

  def setup(self):
    config.set_user_agent_info([
      'Notebook',
      '/'.join(['IPython', IPython.__version__]),
    ])

  def ensure_project(self):
    project_id = get_default_project()
    client_id = self._connection.tokens('self').fetch().client
    ensure_project_exists(self._connection, client_id, project_id)
    return project_id

  @cell_magic
  def experiment(self, _, cell):
    ns = get_ns()

    # pylint: disable=eval-used
    cell_value = eval(cell, ns)
    # pylint: enable=eval-used
    if isinstance(cell_value, dict):
      experiment_body = dict(cell_value)
    else:
      experiment_body = yaml.safe_load(six.StringIO(cell_value))
    self.setup()
    project_id = self.ensure_project()
    experiment_body[PROJECT_KEY] = project_id
    self._experiment = self._connection.experiments().create(**experiment_body)
    print(six.u(
      'Experiment created, view it on the SigOpt dashboard at {app_url}/experiment/{experiment_id}'
    ).format(
      app_url=get_app_url(),
      experiment_id=self._experiment.id))

  def exec_cell(self, name, cell, ns, project_id, suggestion=None):
    with create_global_run(name=name, suggestion=suggestion, project=project_id) as run:
      if config.code_tracking_enabled:
        run.log_source_code(content=cell)
      stream_monitor = SystemOutputStreamMonitor() if config.log_collection_enabled else NullStreamMonitor()
      with stream_monitor:
        # pylint: disable=exec-used
        exec(cell, ns)
        # pylint: enable=exec-used
      stream_data = stream_monitor.get_stream_data()
      if stream_data:
        stdout, stderr = stream_data
        run.update_logs({'stdout': {'content': stdout}, 'stderr': {'content': stderr}})

  @cell_magic
  def run(self, line, cell):
    ns = get_ns()

    name = None
    if line:
      name = line

    self.setup()
    project_id = self.ensure_project()
    self.exec_cell(name, cell, ns, project_id)

  @cell_magic
  def optimize(self, line, cell):
    ns = get_ns()

    if self._experiment is None:
      raise Exception('Please create an experiment first with the %%experiment magic command')

    name = None
    if line:
      name = line

    self.setup()
    project_id = self.ensure_project()

    def loop_body(suggestion):
      self.exec_cell(name, cell, ns, project_id, suggestion=suggestion)

    self._experiment = optimization_loop(self._connection, self._experiment, loop_body)
