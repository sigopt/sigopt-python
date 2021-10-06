import xgboost
from xgboost import DMatrix
import numpy
from sklearn.metrics import accuracy_score, classification_report

from .. import create_run

def run(params, D_train, num_boost_round=10, evals=None, run_options=None):
  """
  Sigopt runs interface
  """
  assert type(D_train) is DMatrix

  num_eval_sets = 0
  if evals:
    num_eval_sets = len(evals) if type(evals) is list else 1

  run = create_run()
  run.log_model("XGBoost")

  # Log data
  run.log_metadata("Dataset columns", D_train.num_col())
  run.log_metadata("Dataset rows", D_train.num_row())


  # check classification or regression

  # set params
  for key in params:
    setattr(run.params, key, params[key])
  run.params.num_boost_round = num_boost_round
  run.log_metadata("Objective", params['objective'])
  bst = xgboost.train(params, D_train, num_boost_round)



  # written assuming single Dmatrix
  # if evals:
  #   D_test = evals
  #   preds = bst.predict(D_test)
  #   preds = numpy.round(preds)
  #   accuracy = accuracy_score(Y_test, preds)
  #   rep = classification_report(Y_test, preds, output_dict=True, zero_division=0)
  #   other_metrics = rep['weighted avg']
  #   run.log_metric("accuracy", accuracy)
  #   run.log_metric("f1", other_metrics['f1-score'])
  #   run.log_metric("recall", other_metrics['recall'])
  #   run.log_metric("precision", other_metrics['precision'])

  return run
