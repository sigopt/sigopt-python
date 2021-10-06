import xgboost
from xgboost import DMatrix
import numpy
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error
from ..context import Context
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


def compute_classification_metrics(run, bst, D_matrix):
  preds = bst.predict(D_matrix)
  preds = numpy.round(preds)
  accuracy = accuracy_score(D_matrix.get_labels(), preds)
  rep = classification_report(D_matrix.get_labels(), preds, output_dict=True, zero_division=0)
  other_metrics = rep['weighted avg']
  run.log_metric("accuracy", accuracy)
  run.log_metric("f1", other_metrics['f1-score'])
  run.log_metric("recall", other_metrics['recall'])
  run.log_metric("precision", other_metrics['precision'])


def compute_regression_metrics(run, bst, D_test):
  pass


def run(params, D_train, num_boost_round=10, evals=None, run_options=None):
  """
  Sigopt integration for XGBoost mirrors the standard XGBoost train interface for the most part, with the option
  for additional arguments. Unlike the usual train interface, run() returns a context object, where context.run
  and context.model are the resulting run and XGBoost model, respectively.
  """
  assert type(D_train) is DMatrix
  assert type(evals) is DMatrix or list

  # Parse evals argument: if DMatrix argument make instead a list of pairs (and will be None by default)
  validation_sets = [(evals, DEFAULT_EVALS_NAME)] if type(evals) is DMatrix else evals

  run = create_run()
  run.log_model("XGBoost")
  run.log_metadata("Dataset columns", D_train.num_col())
  run.log_metadata("Dataset rows", D_train.num_row())
  run.log_metadata("Objective", params['objective'])
  if validation_sets:
    run.log_metadata("Number of Test Sets", len(validation_sets))

  # check classification or regression
  if params['Objective'] is None or params['Objective'].split(':')[0] == 'reg':
    REGRESSION = True
  else:
    CLASSIFICATION = True

  # set and log params, making sure to cross-reference XGB aliases
  for key in params:
    if key in XGB_ALIASES.keys():
      setattr(run.params, XGB_ALIASES[key], params[key])
    else:
      setattr(run.params, key, params[key])
  run.params.num_boost_round = num_boost_round

  # time training
  t_start = time.time()
  bst = xgboost.train(params, D_train, num_boost_round)
  t_train = time.time() - t_start
  run.log_metric("Training time", t_train)


  return Context(run, bst)
