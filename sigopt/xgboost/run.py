import time
import sys
import platform
import copy

import xgboost
# pylint: disable=no-name-in-module
from xgboost import DMatrix

from ..context import Context
from .compute_metrics import compute_classification_metrics, compute_regression_metrics
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


# TODO: (not sure if needed) check that run_option values are all accepted
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


  # check classification or regression
  IS_REGRESSION = True  # XGB does regression by default, if flag false XGB does classification
  if params['objective']:
    if params['objective'].split(':')[0] != 'reg': # Possibly a more robust way of doing this?
      IS_REGRESSION = False

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

  # time training
  t_start = time.time()
  bst = xgboost.train(params, dtrain, num_boost_round)
  t_train = time.time() - t_start
  run.log_metric("Training time", t_train)

  # record training metrics
  if IS_REGRESSION:
    compute_regression_metrics(run, bst, (dtrain, 'Training Set'))
  else:
    compute_classification_metrics(run, bst, (dtrain, 'Training Set'))

  # record validation metrics
  if validation_sets:
    for validation_set in validation_sets:
      if IS_REGRESSION:
        compute_regression_metrics(run, bst, validation_set)
      else:
        compute_classification_metrics(run, bst, validation_set)

  return Context(run, bst)
