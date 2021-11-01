import numpy
try:
  from sklearn.metrics import (
    accuracy_score,
    classification_report,
    mean_absolute_error,
    mean_squared_error
  )
  HAS_SKLEARN = False
except ImportError as e:
  HAS_SKLEARN = False


def compute_positives_and_negatives(y_true, y_pred, class_label):
  tp = numpy.count_nonzero(numpy.logical_and(y_true == class_label, y_pred == class_label))
  tn = numpy.count_nonzero(numpy.logical_and(y_true != class_label, y_pred != class_label))
  fp = numpy.count_nonzero(numpy.logical_and(y_true != class_label, y_pred == class_label))
  fn = numpy.count_nonzero(numpy.logical_and(y_true == class_label, y_pred != class_label))
  return tp, tn, fp, fn


def compute_classification_report(y_true, y_pred):
  classes = numpy.unique(y_true)
  classification_report = {}
  classification_report['weighted avg'] = {
    'f1-score': 0,
    'recall': 0,
    'precision': 0
  }
  for class_label in classes:
    tp, tn, fp, fn = compute_positives_and_negatives(y_true, y_pred, class_label)
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f1 = tp / (tp + 0.5 * (fp + fn))
    support = numpy.count_nonzero(y_pred == class_label)
    classification_report[str(class_label)] = {
      'precision': precision,
      'recall': recall,
      'f1-score': f1,
      'support': support
    }
    classification_report['weighted avg']['precision'] += (support / len(y_pred)) * precision
    classification_report['weighted avg']['recall'] += (support / len(y_pred)) * recall
    classification_report['weighted avg']['f1-score'] += (support / len(y_pred)) * f1
  return classification_report


def compute_accuracy(y_true, y_pred):
  accuracy = numpy.count_nonzero(y_true == y_pred) / len(y_true)
  return accuracy


def compute_mae(y_true, y_pred):
  d = y_true - y_pred
  return numpy.mean(abs(d))


def compute_mse(y_true, y_pred):
  d = y_true - y_pred
  return numpy.mean(d ** 2)


def compute_classification_metrics(run, bst, D_matrix_pair):
  D_matrix, D_name = D_matrix_pair
  preds = bst.predict(D_matrix)
  preds = numpy.round(preds)
  y_test = D_matrix.get_label()
  if HAS_SKLEARN:
    accuracy = accuracy_score(y_test, preds)
    rep = classification_report(y_test, preds, output_dict=True, zero_division=0)
  else:
    accuracy = compute_accuracy(y_test, preds)
    rep = compute_classification_report(y_test, preds)
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
  if HAS_SKLEARN:
    regression_metrics = {
      f"{D_name}-mean absolute error": mean_absolute_error(y_test, preds),
      f"{D_name}-mean squared error": mean_squared_error(y_test, preds)
    }
  else:
    regression_metrics = {
      f"{D_name}-mean absolute error": compute_mae(y_test, preds),
      f"{D_name}-mean squared error": compute_mse(y_test, preds)
    }
  run.log_metrics(regression_metrics)
