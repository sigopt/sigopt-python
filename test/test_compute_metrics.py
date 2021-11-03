from sigopt.xgboost.compute_metrics import (
  compute_classification_report,
  compute_mae,
  compute_mse,
  compute_accuracy
)
from sklearn.metrics import (
  accuracy_score,
  classification_report,
  mean_absolute_error,
  mean_squared_error
)

import numpy as np


def assert_classification_metrics(y_true, y_pred):
  report_compute = compute_classification_report(y_true, y_pred)
  report_sklearn = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
  assert np.abs(report_compute['weighted avg']['precision'] - report_sklearn['weighted avg']['precision']) < 1e-8
  assert np.abs(report_compute['weighted avg']['recall'] - report_sklearn['weighted avg']['recall']) < 1e-8
  assert np.abs(report_compute['weighted avg']['f1-score'] - report_sklearn['weighted avg']['f1-score']) < 1e-8
  assert np.abs(compute_accuracy(y_true, y_pred) - accuracy_score(y_true, y_pred)) < 1e-8


def assert_regression_metrics(y_true, y_pred):
  assert np.abs(mean_absolute_error(y_true, y_pred) - compute_mae(y_true, y_pred)) < 1e-8
  assert np.abs(mean_squared_error(y_true, y_pred) - compute_mse(y_true, y_pred)) < 1e-8


class TestComputeMetrics(object):

  def test_binary(self):
    n = 50
    y_true = np.random.randint(0, 2, n)
    y_pred = np.random.randint(0, 2, n)
    assert_classification_metrics(y_true, y_pred)

  def test_multiclass(self):
    n = 50
    n_class = 3
    y_true = np.random.randint(0, n_class, n)
    y_pred = np.random.randint(0, n_class, n)
    assert_classification_metrics(y_true, y_pred)

  def test_zero_divide_multiclass(self):
    n = 50
    n_class = 3
    y_true = np.random.randint(0, n_class, n)
    y_pred = np.zeros(n)
    assert_classification_metrics(y_true, y_pred)

  def test_zero_divide_binary(self):
    n = 50
    y_true = np.random.randint(0, 2, n)
    y_pred = np.zeros(n)
    assert_classification_metrics(y_true, y_pred)

  def test_regression_metrics(self):
    # Check regression metrics
    n = 100
    y_true = np.random.randn(n)
    y_pred = np.random.randn(n)
    assert_regression_metrics(y_true, y_pred)
