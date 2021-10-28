import platform
import random

from sigopt.xgboost.run import PARAMS_LOGGED_AS_METADATA, run
from sklearn import datasets
from sklearn.model_selection import train_test_split
import xgboost as xgb

iris = datasets.load_iris()
X = iris.data
y = iris.target
num_class = 3
X_train, X_test, Y_train, Y_test = train_test_split(X, y, test_size=0.2)
D_train = xgb.DMatrix(X_train, label=Y_train)
D_test = xgb.DMatrix(X_test, label=Y_test)


POSSIBLE_PARAMETERS = {
  'eta': 10 ** random.uniform(-4, 1),
  'gamma': random.uniform(0, 4),
  'max_depth': random.randint(1, 5),
  'min_child_weight': random.uniform(0, 3),
  'num_class': num_class,
  'lambda': random.uniform(1, 3),
  'alpha': 10 ** random.uniform(-4, 0),
  'objective': random.choice(['multi:softmax', 'multi:softprob']),
  'tree_method': random.choice(['hist', 'exact', 'approx', 'auto']),
  'eval_metric': ['mlogloss', 'merror'],
}

def _form_random_run_params():
  random_subset_size = random.randint(1, len(POSSIBLE_PARAMETERS))
  subset_keys = random.sample(POSSIBLE_PARAMETERS.keys(), random_subset_size)
  if 'num_class' not in subset_keys:
    subset_keys.append('num_class')
  subset_param = {k: POSSIBLE_PARAMETERS[k] for k in subset_keys}
  return dict(
    params=subset_param,
    dtrain=D_train,
    evals=[(D_test, 'test0')],
    num_boost_round=random.randint(3, 15),
  )

class TestXGBoost(object):
  def _verify_parameter_logging(self, run, param):
    for p in params.keys():
      if p in PARAMS_LOGGED_AS_METADATA:
        assert param[p] == run.assignments[p]
      else:
        if not instance(param[p], list):
          assert param[p] == run.metadata[p]
        else:
          assert str(param[p]) == run.metadata[p]

  def test_run(self):
    xgb_params = _form_random_run_params()
    ctx = sigopt.xgboost.run(**xgb_params)
    run = sigopt.get_run(ctx.run.id)
    assert run.metadata['Dataset columns'] == 4
    assert run.metadata['Dataset rows'] == 120
    assert run.metadata['Number of Test Sets'] == 2
    assert run.metadata['Python Version'] == platform.python_version()
    assert run.metadata['XGBoost Version'] == xgb.__version__
    self._verify_parametr_logging()
