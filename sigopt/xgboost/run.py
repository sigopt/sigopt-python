import platform

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


def parse_run_options(run_options):
  if run_options:
    assert run_options.keys() <= DEFAULT_RUN_OPTIONS.keys(), 'Unsupported argument inside run_options'
  run_options_parsed = {**DEFAULT_RUN_OPTIONS, **run_options} if run_options else DEFAULT_RUN_OPTIONS
  return run_options_parsed


class XGBRun:

  def __init__(self, params, dtrain, num_boost_round, evals, run_options):
    self.params = params
    self.dtrain = dtrain
    self.num_boost_round = num_boost_round
    self.evals = evals
    self.run_options_parsed = parse_run_options(run_options)
    self.validation_sets = [(evals, DEFAULT_EVALS_NAME)] if isinstance(evals, DMatrix) else evals
    self.run = None

  def make_run(self):
    if self.run_options_parsed['run']:
      self.run = self.run_options_parsed['run']
    else:
      self.run = create_run()

  def log_metadata(self):
    if self.run_options_parsed['log_sys_info']:
      python_version = platform.python_version()
      self.run.log_metadata("Python Version", python_version)
      self.run.log_metadata("XGBoost Version", xgboost.__version__)
    self.run.log_model("XGBoost")
    self.run.log_metadata("_IS_XGB", 'True')
    self.run.log_metadata("Dataset columns", self.dtrain.num_col())
    self.run.log_metadata("Dataset rows", self.dtrain.num_row())
    if 'objective' in self.params:
      self.run.log_metadata("Objective", self.params['objective'])
    if 'eval_metric' in self.params:
      self.run.log_metadata("Objective", self.params['eval_metric'])
    if self.validation_sets:
      self.run.log_metadata("Number of Test Sets", len(self.validation_sets))
      for pair in self.validation_sets:
        self.run.log_dataset(pair[1])

  def log_params(self):
    # set and log params, making sure to cross-reference XGB aliases
    self.run.params.update(self.params)
    self.run.params.num_boost_round = self.num_boost_round

  def train_xgb(self):
    # train XGB, log stdout/err if necessary
    stream_monitor = SystemOutputStreamMonitor()
    with stream_monitor:
      bst = xgboost.train(self.params, self.dtrain, self.num_boost_round)
    stream_data = stream_monitor.get_stream_data()
    if stream_data:
      stdout, stderr = stream_data
      log_dict = {}
      if self.run_options_parsed['log_stdout']:
        log_dict["stdout"] = stdout
      if self.run_options_parsed['log_stderr']:
        log_dict["stderr"] = stderr
      self.run.set_logs(log_dict)
    return bst


def run(params, dtrain, num_boost_round=10, evals=None, run_options=None):
  """
  Sigopt integration for XGBoost mirrors the standard XGBoost train interface for the most part, with the option
  for additional arguments. Unlike the usual train interface, run() returns a context object, where context.run
  and context.model are the resulting run and XGBoost model, respectively.
  """

  if evals:
    assert isinstance(evals, (DMatrix, list)), 'evals must be a DMatrix or list of (DMatrix, string) pairs'

  _run = XGBRun(params, dtrain, num_boost_round, evals, run_options)
  _run.make_run()
  _run.log_metadata()
  _run.log_params()
  bst = _run.train_xgb()
  return Context(_run.run, bst)
