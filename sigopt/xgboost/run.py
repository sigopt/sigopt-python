import xgboost
from xgboost import DMatrix

from ..context import Context
from .compute_metrics import compute_classification_metrics, compute_regression_metrics
from .. import create_run
import time

DEFAULT_EVALS_NAME = 'Test Set'
XGB_ALIASES = \
  {
     'learning_rate': 'eta',
     'min_split_loss': 'gamma',
     'reg_lambda': 'lambda',
     'reg_alpha': 'alpha'
  }

def run(params, dtrain, num_boost_round=10, evals=None, run_options=None, run=None):
  """
  Sigopt integration for XGBoost mirrors the standard XGBoost train interface for the most part, with the option
  for additional arguments. Unlike the usual train interface, run() returns a context object, where context.run
  and context.model are the resulting run and XGBoost model, respectively.
  """
  assert isinstance(evals, DMatrix) or isinstance(evals, list)

  # Parse evals argument: if DMatrix argument make instead a list of a singleton pair (and will be None by default)
  validation_sets = [(evals, DEFAULT_EVALS_NAME)] if isinstance(evals, DMatrix) else evals

  if run is None:
    run = create_run()

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
  for key in params:
    if key in XGB_ALIASES.keys():
      setattr(run.params, XGB_ALIASES[key], params[key])
    else:
      setattr(run.params, key, params[key])
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
  for validation_set in validation_sets:
    if IS_REGRESSION:
      compute_regression_metrics(run, bst, validation_set)
    else:
      compute_classification_metrics(run, bst, validation_set)

  return Context(run, bst)
