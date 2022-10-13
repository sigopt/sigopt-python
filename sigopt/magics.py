# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click
import http
import io
import sys
import yaml
import IPython
from IPython.core.magic import (
  Magics,
  cell_magic,
  line_magic,
  magics_class,
)

from .config import config
from .cli.commands.config import API_TOKEN_PROMPT, LOG_COLLECTION_PROMPT, CELL_TRACKING_PROMPT
from .log_capture import NullStreamMonitor, SystemOutputStreamMonitor
from .run_context import global_run_context
from .factory import SigOptFactory
from .defaults import get_default_project
from .validate import validate_aiexperiment_input, ValidationError
from .sigopt_logging import print_logger
from .exception import ApiException


def get_ns():
  # NOTE(taylor): inspired by https://github.com/ipython/ipython/blob/master/IPython/core/interactiveshell.py
  # Walk up the stack trace until we find the 'exit' command
  stack_depth = 1
  while True:
    frame = sys._getframe(stack_depth)
    f_locals = frame.f_locals
    try:
      if isinstance(f_locals['exit'], IPython.core.autocall.ExitAutocall):
        return f_locals
    except KeyError:
      pass
    stack_depth += 1

@magics_class
class SigOptMagics(Magics):
  def __init__(self, shell):
    super().__init__(shell)
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
      validated = validate_aiexperiment_input(experiment_body)
    except ValidationError as validation_error:
      print_logger.error("ValidationError: %s", str(validation_error))
      return
    try:
      self._experiment = self._factory.create_prevalidated_aiexperiment(validated)
    except ApiException as api_exception:
      if api_exception.status_code == http.HTTPStatus.BAD_REQUEST:
        print_logger.error("ApiException: %s", str(api_exception))

  def exec_cell(self, run_context, cell, ns):
    global_run_context.set_run_context(run_context)
    try:
      if config.cell_tracking_enabled:
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

  @line_magic
  def sigopt(self, line):
    command = line.strip()
    if command == "config":
      api_token = click.prompt(API_TOKEN_PROMPT, hide_input=True)
      enable_log_collection = click.confirm(LOG_COLLECTION_PROMPT, default=False)
      enable_code_tracking = click.confirm(CELL_TRACKING_PROMPT, default=False)
      config.persist_configuration_options({
        config.API_TOKEN_KEY: api_token,
        config.CELL_TRACKING_ENABLED_KEY: enable_code_tracking,
        config.LOG_COLLECTION_ENABLED_KEY: enable_log_collection,
      })
      self._factory.connection.set_client_token(api_token)
    else:
      raise ValueError(f"Unknown sigopt command: {command}")
