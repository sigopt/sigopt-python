import numpy


def compute_positives_and_negatives(y_true, y_pred, class_label):
  y_true_equals = y_true == class_label
  y_true_notequals = y_true != class_label
  y_pred_equals = y_pred == class_label
  y_pred_notequals = y_pred != class_label
  tp = numpy.count_nonzero(numpy.logical_and(y_true_equals, y_pred_equals))
  tn = numpy.count_nonzero(numpy.logical_and(y_true_notequals, y_pred_notequals))
  fp = numpy.count_nonzero(numpy.logical_and(y_true_notequals, y_pred_equals))
  fn = numpy.count_nonzero(numpy.logical_and(y_true_equals, y_pred_notequals))
  return tp, tn, fp, fn


def compute_accuracy(y_true, y_pred):
  accuracy = numpy.count_nonzero(y_true == y_pred) / len(y_true)
  return accuracy


def compute_classification_report(y_true, y_pred):
  classes = numpy.unique(y_true)
  classification_report = {}
  classification_report['weighted avg'] = {
    'f1-score': 0,
    'recall': 0,
    'precision': 0
  }
  for class_label in classes:
    tp, _, fp, fn = compute_positives_and_negatives(y_true, y_pred, class_label)
    precision = tp / (tp + fp) if (tp + fp) != 0 else 0
    recall = tp / (tp + fn) if (tp + fn) != 0 else 0
    f1 = tp / (tp + 0.5 * (fp + fn)) if (tp + 0.5 * (fp + fn)) != 0 else 0
    support = numpy.count_nonzero(y_true == class_label)
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


def compute_mae(y_true, y_pred):
  d = y_true - y_pred
  return numpy.mean(abs(d))


def compute_mse(y_true, y_pred):
  d = y_true - y_pred
  return numpy.mean(d ** 2)


def compute_classification_metrics(run, bst, D_matrix_pair):
  D_matrix, D_name = D_matrix_pair
  preds = bst.predict(D_matrix)
  # Check shape of preds
  if len(preds.shape) == 2:
    preds = numpy.argmax(preds, axis=1)
  else:
    preds = numpy.round(preds)
  y_test = D_matrix.get_label()
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
  regression_metrics = {
    f"{D_name}-mean absolute error": compute_mae(y_test, preds),
    f"{D_name}-mean squared error": compute_mse(y_test, preds)
  }
  run.log_metrics(regression_metrics)
