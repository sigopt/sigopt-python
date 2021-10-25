import xgboost as xgb
from sklearn import datasets
from sklearn.model_selection import train_test_split
import sigopt.xgboost
import numpy as np

iris = datasets.load_iris()
X = iris.data
y = iris.target
num_class = len(np.unique(y))
X_train, X_test, Y_train, Y_test = train_test_split(X, y, test_size=0.2)
D_train = xgb.DMatrix(X_train, label=Y_train)
D_test = xgb.DMatrix(X_test, label=Y_test)

xgb_params = dict(
  params={
    'eta': 0.3,
    'max_depth': 7,
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
    assert run.metadata['_IS_XGB'] == "True"
