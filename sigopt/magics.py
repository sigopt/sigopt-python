import http
import io
import sys
import yaml
import IPython
from IPython.core.magic import (
  Magics,
  cell_magic,
  magics_class,
)

from .config import config
from .interface import Connection
from .log_capture import NullStreamMonitor, SystemOutputStreamMonitor
from .run_context import global_run_context
from .factory import SigOptFactory
from .defaults import get_default_project
from .validate import validate_experiment_input, ValidationError
from .logging import print_logger
from .exception import ApiException


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
    self._factory = SigOptFactory(get_default_project())

  def setup(self):
    config.set_user_agent_info([
      'Notebook',
      '/'.join(['IPython', IPython.__version__]),
    ])

  @cell_magic
  def experiment(self, _, cell):
    ns = get_ns()

    # pylint: disable=eval-used
    cell_value = eval(cell, ns)
    # pylint: enable=eval-used
    if isinstance(cell_value, dict):
      experiment_body = dict(cell_value)
    else:
      experiment_body = yaml.safe_load(io.StringIO(cell_value))
    self.setup()
    try:
      validated = validate_experiment_input(experiment_body)
    except ValidationError as validation_error:
      print_logger.error("ValidationError: %s", str(validation_error))
      return
    try:
      self._experiment = self._factory.create_prevalidated_experiment(validated)
    except ApiException as api_exception:
      if api_exception.status_code == http.HTTPStatus.BAD_REQUEST:
        print_logger.error("ApiException: %s", str(api_exception))

  def exec_cell(self, run_context, cell, ns):
    global_run_context.set_run_context(run_context)
    try:
      if config.code_tracking_enabled:
        run_context.log_source_code(content=cell)
      stream_monitor = SystemOutputStreamMonitor() if config.log_collection_enabled else NullStreamMonitor()
      with stream_monitor:
        # pylint: disable=exec-used
        exec(cell, ns)
        # pylint: enable=exec-used
      stream_data = stream_monitor.get_stream_data()
      if stream_data:
        stdout, stderr = stream_data
        run_context.set_logs({'stdout': stdout, 'stderr': stderr})
    finally:
      global_run_context.clear_run_context()

  @cell_magic
  def run(self, line, cell):
    ns = get_ns()

    name = None
    if line:
      name = line

    self.setup()
    run_context = self._factory.create_run(name=name)
    with run_context:
      self.exec_cell(run_context, cell, ns)

  @cell_magic
  def optimize(self, line, cell):
    ns = get_ns()

    if self._experiment is None:
      raise Exception('Please create an experiment first with the %%experiment magic command')

    name = None
    if line:
      name = line

    self.setup()

    for run_context in self._experiment.loop(name=name):
      with run_context:
        self.exec_cell(run_context, cell, ns)
