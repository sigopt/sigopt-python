from sigopt.xgboost.compute_metrics import (
  _compute_classification_report,
  compute_mae,
  compute_mse,
  _compute_accuracy
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
preds = np.round(preds)


class TestComputeMetrics(object):
  def test_classification_metrics(self):
    report_compute = _compute_classification_report(Y_test, preds)
    report_sklearn = classification_report(Y_test, preds, output_dict=True, zero_division=0)

    # Check classification metrics
    assert np.abs(report_compute['weighted avg']['precision'] - report_sklearn['weighted avg']['precision']) < 1e-8
    assert np.abs(report_compute['weighted avg']['recall'] - report_sklearn['weighted avg']['recall']) < 1e-8
    assert np.abs(report_compute['weighted avg']['f1-score'] - report_sklearn['weighted avg']['f1-score']) < 1e-8
    assert np.abs(_compute_accuracy(Y_test, preds) - accuracy_score(Y_test, preds)) < 1e-8

  def test_regression_metrics(self):
    # Check regression metrics
    assert np.abs(mean_absolute_error(Y_test, preds) - compute_mae(Y_test, preds)) < 1e-8
    assert np.abs(mean_squared_error(Y_test, preds) - compute_mse(Y_test, preds)) < 1e-8
