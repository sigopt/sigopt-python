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
from sklearn import datasets
from sklearn.model_selection import train_test_split
import xgboost as xgb
import numpy as np


def assert_classification_metrics(y_true, y_pred):
  report_compute = compute_classification_report(y_true, y_pred)
  report_sklearn = classification_report(y_true, y_pred, output_dict=True, zero_division=0)

  # Check classification metrics
  assert np.abs(report_compute['weighted avg']['precision'] - report_sklearn['weighted avg']['precision']) < 1e-8
  assert np.abs(report_compute['weighted avg']['recall'] - report_sklearn['weighted avg']['recall']) < 1e-8
  assert np.abs(report_compute['weighted avg']['f1-score'] - report_sklearn['weighted avg']['f1-score']) < 1e-8
  assert np.abs(compute_accuracy(y_true, y_pred) - accuracy_score(y_true, y_pred)) < 1e-8


def assert_regression_metrics(y_true, y_pred):
  assert np.abs(mean_absolute_error(y_true, y_pred) - compute_mae(y_true, y_pred)) < 1e-8
  assert np.abs(mean_squared_error(y_true, y_pred) - compute_mse(y_true, y_pred)) < 1e-8


class TestComputeMetrics(object):
  def test_classification_metrics_xgb(self):
    iris = datasets.load_iris()
    X = iris.data
    y = iris.target
    num_class = 3
    X_train, X_test, Y_train, Y_test = train_test_split(X, y, test_size=0.3)
    D_train = xgb.DMatrix(X_train, label=Y_train)
    D_test = xgb.DMatrix(X_test, label=Y_test)

    params = {
      'eta': 0.3,
      'num_class': num_class,
      'objective': 'multi:softmax'
    }
    bst = xgb.train(params, D_train)
    preds = bst.predict(D_test)
    xgb_preds = np.round(preds)
    xgb_true = Y_test
    assert_classification_metrics(xgb_true, xgb_preds)

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
