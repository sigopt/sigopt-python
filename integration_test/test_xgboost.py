import xgboost as xgb
from sklearn import datasets
from sklearn.model_selection import train_test_split
import sigopt.xgboost
import numpy as np
import xgboost as xgb
import platform

iris = datasets.load_iris()
X = iris.data
y = iris.target
num_class = len(np.unique(y))
X_train, X_test, Y_train, Y_test = train_test_split(X, y, test_size=0.2)
D_train = xgb.DMatrix(X_train, label=Y_train)
D_test = xgb.DMatrix(X_test, label=Y_test)

xgb_params = dict(
  params={
    'eta': np.random.uniform(0, 1),
    'max_depth': np.random.choice([2, 3, 4, 5]),
    'num_class': num_class,
    'objective': 'multi:softmax',
    'tree_method': 'hist',
    'eval_metric': ['mlogloss', 'merror']
  },
  dtrain=D_train,
  evals=[(D_test, 'test0'), (D_test, 'test1')],
  num_boost_round=10,
)

class TestXGBoost(object):
  def test_run(self):
    ctx = sigopt.xgboost.run(**xgb_params)
    run = sigopt.get_run(ctx.run.id)
    print(run)

    assert run.metadata['Dataset columns'] == 4
    assert run.metadata['Dataset rows'] == 120
    assert run.metadata['Eval Metric'] == "['mlogloss', 'merror']"
    assert run.metadata['Number of Test Sets'] == 2
    assert run.metadata['Objective'] == "multi:softmax"
    assert run.metadata['Python Version'] == platform.python_version()
    assert run.metadata['XGBoost Version'] == xgb.__version__
    assert run.assignments['eta'] == xgb_params['params']['eta']
    assert run.assignments['max_depth'] == xgb_params['params']['max_depth']
    assert run.assignments['num_class'] == xgb_params['params']['num_class']
    assert run.assignments['objective'] == xgb_params['params']['objective']
    assert run.assignments['tree_method'] == xgb_params['params']['tree_method']
    assert run.assignments['num_boost_round'] == xgb_params['num_boost_round']
