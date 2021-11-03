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


class TestComputeMetrics(object):
  def test_compute_classification_metrics(self):
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
    bst = ctx.model

    # compute sklearn-based metrics
    preds = bst.predict(D_test)
    xgb_preds = np.round(preds)
    xgb_true = Y_test
    report_sklearn = classification_report(xgb_true, xgb_preds, output_dict=True, zero_division=0)
    accuracy_sklearn = accuracy_score(xgb_true, xgb_preds)

    # compare metrics
    run = sigopt.get_run(ctx.run.id)
    assert np.abs(run.values['test0-precision'].value - report_sklearn['weighted avg']['precision']) < 1e-8
    assert np.abs(run.values['test0-recall'].value - report_sklearn['weighted avg']['recall']) < 1e-8
    assert np.abs(run.values['test0-F1'].value - report_sklearn['weighted avg']['f1-score']) < 1e-8
    assert np.abs(run.values['test0-accuracy'].value - accuracy_sklearn) < 1e-8

  def test_compute_regression_metrics(self):
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
    bst = ctx.model

    # compute sklearn-based metrics
    preds = bst.predict(D_test)
    xgb_preds = np.round(preds)
    xgb_true = Y_test
    mae = mean_absolute_error(xgb_true, xgb_preds)
    mse = mean_squared_error(xgb_true, xgb_preds)

    # compare metrics
    run = sigopt.get_run(ctx.run.id)
    assert np.abs(run.values['test0-mean absolute error'].value - mae) < (1e-8 / mae)
    assert np.abs(run.values['test0-mean squared error'].value - mse) < (1e-8 / mae)
