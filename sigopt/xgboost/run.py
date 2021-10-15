import time
import sys
import platform
import copy

import xgboost
# pylint: disable=no-name-in-module
from xgboost import DMatrix

from ..context import Context
from ..log_capture import SystemOutputStreamMonitor
from .. import create_run

DEFAULT_EVALS_NAME = 'Test Set'
DEFAULT_RUN_OPTIONS = {
  'log_sys_info': True,
  'log_stdout': True,
  'log_stderr': True,
  'run': None
}
XGB_ALIASES = \
  {
     'learning_rate': 'eta',
     'min_split_loss': 'gamma',
     'reg_lambda': 'lambda',
     'reg_alpha': 'alpha'
  }


def parse_run_options(run_options):
  if run_options:
    assert run_options.keys() <= DEFAULT_RUN_OPTIONS.keys(), 'Unsupported argument inside run_options'
  run_options_parsed = {**DEFAULT_RUN_OPTIONS, **run_options} if run_options else DEFAULT_RUN_OPTIONS
  return run_options_parsed


def run(params, dtrain, num_boost_round=10, evals=None, run_options=None):
  """
  Sigopt integration for XGBoost mirrors the standard XGBoost train interface for the most part, with the option
  for additional arguments. Unlike the usual train interface, run() returns a context object, where context.run
  and context.model are the resulting run and XGBoost model, respectively.
  """

  if evals:
    assert isinstance(evals, (DMatrix, list)), 'evals must be a DMatrix or list of (DMatrix, string) pairs'
  run_options_parsed = parse_run_options(run_options)


  # Parse evals argument: if DMatrix argument make instead a list of a singleton pair (and will be None by default)
  validation_sets = [(evals, DEFAULT_EVALS_NAME)] if isinstance(evals, DMatrix) else evals

  if run_options_parsed['run']:
    run = run_options_parsed['run']
  else:
    run = create_run()

  # Log metadata
  if run_options_parsed['log_sys_info']:
    python_version = platform.python_version()
    run.log_metadata("Python Version", python_version)
    run.log_metadata("XGBoost Version", xgboost.__version__)
  run.log_model("XGBoost")
  run.log_metadata("_IS_XGB", 'True')
  run.log_metadata("Dataset columns", dtrain.num_col())
  run.log_metadata("Dataset rows", dtrain.num_row())
  run.log_metadata("Objective", params['objective'])
  if validation_sets:
    run.log_metadata("Number of Test Sets", len(validation_sets))

  # set and log params, making sure to cross-reference XGB aliases
  for key, value in params.items():
    log_value = copy.deepcopy(value) # overkill for most things but this value may be a list for whatever reason
    if isinstance(log_value, (list, bool)):
      log_value = str(log_value)
    if key in XGB_ALIASES.keys():
      setattr(run.params, XGB_ALIASES[key], log_value)
    else:
      setattr(run.params, key, log_value)
  run.params.num_boost_round = num_boost_round

  # train XGB, log stdout/err if necessary
  stream_monitor = SystemOutputStreamMonitor()
  with stream_monitor:
    bst = xgboost.train(params, dtrain, num_boost_round)
  stream_data = stream_monitor.get_stream_data()
  if stream_data:
    stdout, stderr = stream_data
    log_dict = {}
    if run_options_parsed['log_stdout']:
      log_dict["stdout"] = stdout
    if run_options_parsed['log_stderr']:
      log_dict["stderr"] = stderr
    run.set_logs(log_dict)

  return Context(run, bst)
