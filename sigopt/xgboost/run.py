import platform

import xgboost
# pylint: disable=no-name-in-module
from xgboost import DMatrix
import math

from ..context import Context
from ..log_capture import SystemOutputStreamMonitor
from .. import create_run

DEFAULT_EVALS_NAME = 'Test Set'
DEFAULT_RUN_OPTIONS = {
  'log_sys_info': True,
  'log_stdout': True,
  'log_stderr': True,
  'log_checkpoints': True,
  'run': None
}
MIN_CHECKPOINT_PERIOD = 5
MAX_NUM_CHECKPOINTS = 200
PARAMS_LOGGED_AS_METADATA = [
  'eval_metric',
  'objective',
  'updater',
]


def parse_run_options(run_options):
  if run_options:
    assert run_options.keys() <= DEFAULT_RUN_OPTIONS.keys(), 'Unsupported argument inside run_options'
  run_options_parsed = {**DEFAULT_RUN_OPTIONS, **run_options} if run_options else DEFAULT_RUN_OPTIONS
  return run_options_parsed


class SigOptCheckpointCallback(xgboost.callback.TrainingCallback):
  def __init__(self, run, period=1):
    self.run = run
    self.period = period
    self._latest = None
    super().__init__()

  def after_iteration(self, model, epoch, evals_log):
    if not evals_log:
      return False

    checkpoint_logs = {}
    for data, metric in evals_log.items():
      for metric_name, log in metric.items():
        if isinstance(log[-1], tuple):
          score = log[-1][0]
        else:
          score = log[-1]
        checkpoint_logs.update({'-'.join((data, metric_name)): score})
    if (epoch % self.period) == 0 or self.period == 1:
      self.run.log_checkpoint(checkpoint_logs)
      self._latest = None
    else:
      self._latest = checkpoint_logs

    return False

  def after_training(self, model):
    if self._latest is not None:
      self.run.log_checkpoint(self._latest)
    return model


class XGBRun:

  def __init__(self, params, dtrain, num_boost_round, evals, verbose_eval, callbacks, run_options):
    self.params = params
    self.dtrain = dtrain
    self.num_boost_round = num_boost_round
    self.evals = evals
    self.verbose_eval = verbose_eval
    self.callbacks = callbacks
    self.validation_sets = [(evals, DEFAULT_EVALS_NAME)] if isinstance(evals, DMatrix) else evals
    self.run_options_parsed = parse_run_options(run_options)
    self.run = None

  def form_callbacks(self):
    # if no validation set, checkpointing not possible
    if not (self.run_options_parsed['log_checkpoints'] and self.validation_sets):
      return

    if self.callbacks is None:
      self.callbacks = []
    period = MIN_CHECKPOINT_PERIOD
    if self.callbacks:
      for cb in self.callbacks:
        if isinstance(cb, xgboost.callback.EvaluationMonitor):
          period = cb.period
    if self.verbose_eval:
      period = 1 if self.verbose_eval is True else self.verbose_eval
    period = max(period, math.ceil((self.num_boost_round + 1) / MAX_NUM_CHECKPOINTS))
    sigopt_checkpoint_callback = SigOptCheckpointCallback(self.run, period=period)
    self.callbacks.append(sigopt_checkpoint_callback)

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
    for name in PARAMS_LOGGED_AS_METADATA:
      if name in self.params:
        self.run.log_metadata(name, self.params[name])
    if self.validation_sets:
      self.run.log_metadata("Number of Test Sets", len(self.validation_sets))
      for pair in self.validation_sets:
        self.run.log_dataset(pair[1])

  def log_params(self):
    for name in self.params.keys():
      if name not in PARAMS_LOGGED_AS_METADATA:
        self.run.params.update({name: self.params[name]})

    self.run.params.num_boost_round = self.num_boost_round

  def train_xgb(self):
    # train XGB, log stdout/err if necessary
    stream_monitor = SystemOutputStreamMonitor()
    with stream_monitor:
      xgb_args = {
        'params': self.params,
        'dtrain': self.dtrain,
        'num_boost_round': self.num_boost_round,
        'verbose_eval': self.verbose_eval,
      }
      if self.validation_sets:
        xgb_args['evals'] = self.validation_sets
      if self.callbacks:
        xgb_args['callbacks'] = self.callbacks
      bst = xgboost.train(
        **xgb_args
      )
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


def run(params, dtrain, num_boost_round=10, evals=None, callbacks=None, verbose_eval=True, run_options=None):
  """
  Sigopt integration for XGBoost mirrors the standard XGBoost train interface for the most part, with the option
  for additional arguments. Unlike the usual train interface, run() returns a context object, where context.run
  and context.model are the resulting run and XGBoost model, respectively.
  """

  if evals:
    assert isinstance(evals, (DMatrix, list)), 'evals must be a DMatrix or list of (DMatrix, string) pairs'

  _run = XGBRun(params, dtrain, num_boost_round, evals, verbose_eval, callbacks, run_options)
  _run.make_run()
  _run.log_metadata()
  _run.log_params()
  _run.form_callbacks()
  bst = _run.train_xgb()
  return Context(_run.run, bst)
