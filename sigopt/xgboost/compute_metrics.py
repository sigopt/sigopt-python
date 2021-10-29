import numpy
from sklearn.metrics import (
  accuracy_score,
  classification_report,
  mean_absolute_error,
  mean_squared_error
)


def compute_classification_metrics(run, bst, D_matrix_pair):
  D_matrix, D_name = D_matrix_pair
  preds = bst.predict(D_matrix)
  preds = numpy.round(preds)
  y_test = D_matrix.get_label()
  accuracy = accuracy_score(y_test, preds)
  rep = classification_report(y_test, preds, output_dict=True, zero_division=0)
  other_metrics = rep['weighted avg']
  classification_metrics = {
    f"{D_name}-accuracy" : accuracy,
    f"{D_name}-F1" : other_metrics['f1-score'],
    f"{D_name}-recall": other_metrics['recall'],
    f"{D_name}-precision": other_metrics['precision']
  }
  run.log_metrics(classification_metrics)


def compute_regression_metrics(run, bst, D_matrix_pair):
  D_matrix, D_name = D_matrix_pair
  preds = bst.predict(D_matrix)
  preds = numpy.round(preds)
  y_test = D_matrix.get_label()
  regression_metrics = {
    f"{D_name}-mean absolute error": mean_absolute_error(y_test, preds),
    f"{D_name}-mean squared error": mean_squared_error(y_test, preds)
  }
  run.log_metrics(regression_metrics)
