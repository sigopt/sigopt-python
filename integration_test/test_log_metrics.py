import sigopt.xgboost
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


class TestLogMetrics(object):
  def test_log_classification_metrics(self):
    params = {
      'eta': 0.3,
      'num_class': num_class,
      'objective': 'multi:softmax'
    }
    xgb_params = {
      'params': params,
      'dtrain': D_train,
      'evals': [(D_test, 'test0')],
    }
    ctx = sigopt.xgboost.run(**xgb_params)
    run = sigopt.get_run(ctx.run.id)
    assert run.values['test0-accuracy']
    assert run.values['test0-F1']
    assert run.values['test0-precision']
    assert run.values['test0-recall']
    assert run.values['Training Set-accuracy']
    assert run.values['Training Set-F1']
    assert run.values['Training Set-precision']
    assert run.values['Training Set-recall']
    assert run.values['Training time']

  def test_log_regression_metrics(self):
    params = {
      'eta': 0.3,
      'objective': 'reg:squarederror'
    }
    xgb_params = {
      'params': params,
      'dtrain': D_train,
      'evals': [(D_test, 'test0')],
    }
    ctx = sigopt.xgboost.run(**xgb_params)
    run = sigopt.get_run(ctx.run.id)
    assert run.values['test0-mean absolute error']
    assert run.values['test0-mean squared error']
    assert run.values['Training Set-mean absolute error']
    assert run.values['Training Set-mean squared error']
    assert run.values['Training time']
