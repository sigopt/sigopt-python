import itertools
import platform
import pytest
import random

import sigopt.xgboost
from sigopt.xgboost.run import (
  DEFAULT_CHECKPOINT_PERIOD,
  DEFAULT_EVALS_NAME,
  DEFAULT_TRAINING_NAME,
  PARAMS_LOGGED_AS_METADATA,
  XGB_INTEGRATION_KEYWORD,
)
from sklearn import datasets
from sklearn.model_selection import train_test_split
import numpy
import xgboost as xgb

POSSIBLE_PARAMETERS = {
  'eta': 10 ** random.uniform(-4, 1),
  'gamma': random.uniform(0, 4),
  'max_depth': random.randint(1, 5),
  'min_child_weight': random.uniform(0, 3),
  'lambda': random.uniform(1, 3),
  'alpha': 10 ** random.uniform(-4, 0),
  'tree_method': random.choice(['hist', 'exact', 'approx', 'auto']),
}

CLASSIFICATION_METRIC_NAMES = (
  'accuracy',
  'F1',
  'precision',
  'recall',
)
REGRESSION_METRIC_NAMES = (
  'mean absolute error',
  'mean squared error',
)

def _create_random_dataset(task='binary'):
  if task == 'binary':
    n_samples = random.randint(180, 300)
    n_features = random.randint(5, 25)
    n_classes = 2

    return datasets.make_classification(
      n_samples=n_samples,
      n_features=n_features,
      n_classes=n_classes,
    )
  elif task == 'multiclass':
    n_samples = random.randint(180, 300)
    n_classes = random.randint(3, 8)
    n_informative = random.randint(2 * n_classes, 20)
    n_features = random.randint(n_informative + 2, 40)

    return datasets.make_classification(
      n_samples=n_samples,
      n_features=n_features,
      n_informative=n_informative,
      n_classes=n_classes,
    )
  else:
    n_samples = random.randint(200, 500)
    n_features = random.randint(50, 100)
    n_informative = random.randint(10, n_features - 2)

    return datasets.make_regression(
      n_samples=n_samples,
      n_features=n_features,
      n_informative=n_informative,
      noise=0.2,
    )

def _create_random_metric_objective(task='binary'):
  if task == 'binary':
    return {
      'objective': random.choice(['binary:logistic', 'binary:hinge', 'binary:logitraw']),
      'eval_metric': ['logloss', 'aucpr', 'error'],
    }
  elif task == 'multiclass':
    return {
      'objective': random.choice(['multi:softmax', 'multi:softprob']),
      'eval_metric': ['mlogloss', 'merror'],
    }
  else:
    return {
      'objective': random.choice(['reg:squarederror', 'reg:pseudohubererror']),
      'eval_metric': ['rmse', 'mae', 'mape'],
    }


def _form_random_run_params(task):
  X, y = _create_random_dataset(task)
  X_train, X_test, Y_train, Y_test = train_test_split(X, y, test_size=0.2)
  D_train = xgb.DMatrix(X_train, label=Y_train)
  D_test = xgb.DMatrix(X_test, label=Y_test)

  possible_params = POSSIBLE_PARAMETERS
  random_subset_size = random.randint(1, len(possible_params))
  subset_keys = random.sample(possible_params.keys(), random_subset_size)
  subset_params = {k: possible_params[k] for k in subset_keys}
  subset_params.update(_create_random_metric_objective(task))
  if task == 'multiclass':
    subset_params.update({'num_class': len(numpy.unique(y))})

  run_options = {'name': f'dev-integration-test-{task}'}

  return dict(
    params=subset_params,
    dtrain=D_train,
    evals=[(D_test, f'test{n}') for n in range(random.randint(0, 2))],
    num_boost_round=random.randint(3, 15),
    verbose_eval=random.choice([True, False]),
    run_options=run_options,
  )


class TestXGBoost(object):
  def _verify_parameter_logging(self, run):
    params = self.run_params['params']
    for p in params.keys():
      if p not in PARAMS_LOGGED_AS_METADATA:
        assert params[p] == run.assignments[p]
      else:
        if not isinstance(params[p], list):
          assert params[p] == run.metadata[p]
        else:
          assert str(params[p]) == run.metadata[p]
    assert run.assignments['num_boost_round'] == self.run_params['num_boost_round']

  def _verify_metric_logging(self, run):
    data_names = [DEFAULT_TRAINING_NAME]
    if self.run_params['evals']:
      data_names.extend([e[-1] for e in self.run_params['evals']])
    if self.is_classification:
      for d_name, m_name in itertools.product(data_names, CLASSIFICATION_METRIC_NAMES):
        assert 0 <= run.values['-'.join((d_name, m_name))].value <= 1
    else:
      for d_name, m_name in itertools.product(data_names, REGRESSION_METRIC_NAMES):
        assert run.values['-'.join((d_name, m_name))].value >= 0

    if self.run_params['params']['eval_metric']:
      for d_name, m_name in itertools.product(data_names[1:], self.run_params['params']['eval_metric']):
        assert run.values['-'.join((d_name, m_name))]

    assert run.values['Training time'].value > 0

  def _verify_metadata_logging(self, run):
    assert run.metadata['Dataset columns'] == self.run_params['dtrain'].num_col()
    assert run.metadata['Dataset rows'] == self.run_params['dtrain'].num_row()
    if 'evals' in self.run_params and self.run_params['evals'] is not None:
      if isinstance(self.run_params['evals'], list):
        assert run.metadata['Number of Test Sets'] == len(self.run_params['evals'])
      else:
        assert run.metadata['Number of Test Sets'] == 1
    assert run.metadata['Python Version'] == platform.python_version()
    assert run.metadata['XGBoost Version'] == xgb.__version__

  def _verify_feature_importances_logging(self, run, model):
    real_scores = sorted(model.get_score(importance_type='weight').items(), key=lambda x: (x[1], x[0]), reverse=True)
    if real_scores:
      feature_importances = run.sys_metadata['feature_importances']
      saved_scores = sorted(feature_importances['scores'].items(), key=lambda x: (x[1], x[0]), reverse=True)
      assert feature_importances['type'] == 'weight'
      assert saved_scores and len(saved_scores) <= len(real_scores)
      real_scores = real_scores[:len(saved_scores)]
      assert [feature_name for feature_name, _ in real_scores] == [feature_name for feature_name, _ in saved_scores]
      assert numpy.allclose(
        numpy.array([feature_importance for _, feature_importance in real_scores]),
        numpy.array([feature_importance for _, feature_importance in saved_scores]),
      )

  def _verify_miscs_data_logging(self, run):
    if 'name' in self.run_params['run_options']:
      assert run.name == self.run_params['run_options']['name']

    if 'evals' in self.run_params:
      if isinstance(self.run_params['evals'], list):
        assert set(run.datasets) == set([e[1] for e in self.run_params['evals']])
      else:
        assert len(run.datasets) == 1
        assert run.datasets[0] == DEFAULT_EVALS_NAME

    assert XGB_INTEGRATION_KEYWORD in run.dev_metadata
    assert run.dev_metadata[XGB_INTEGRATION_KEYWORD]

  def _verify_checkpoint_logging(self, run):
    if not self.run_params['verbose_evals']:
      assert run.checkpoint_count == (
        self.run_params['num_boost_round'] // DEFAULT_CHECKPOINT_PERIOD + 1 * (
          self.run_params['num_boost_round'] % DEFAULT_CHECKPOINT_PERIOD > 0
        )
      )
    elif self.run_params['verbose_evals'] is True:
      assert run.checkpoint_count == self.run_params['num_boost_round']
    else:
      assert run.checkpoint_count == (
        self.run_params['num_boost_round'] // self.run_params['verbose_evals'] + 1 * (
          self.run_params['num_boost_round'] % self.run_params['verbose_evals'] > 0
        )
      )

  @pytest.mark.parametrize("task", ['binary', 'multiclass', 'regression'])
  def test_run(self, task):
    self.is_classification = True if task in ('binary', 'multiclass') else False
    self.run_params = _form_random_run_params(task)
    ctx = sigopt.xgboost.run(**self.run_params)
    run = sigopt.get_run(ctx.run.id)

    self._verify_metadata_logging(run)
    self._verify_parameter_logging(run)
    self._verify_metric_logging(run)
    self._verify_feature_importances_logging(run, ctx.model)
    self._verify_miscs_data_logging(run)

  def test_run_options_no_logging(self):
    self.run_params = _form_random_run_params(task='binary')
    self.run_params['run_options'].update({
      'log_checkpoints': False,
      'log_feature_importances': False,
      'log_metrics': False,
      'log_params': False,
      'log_stderr': False,
      'log_stdout': False,
    })
    ctx = sigopt.xgboost.run(**self.run_params)
    run = sigopt.get_run(ctx.run.id)

    assert run.checkpoint_count == 0
    assert 'feature_importances' not in run.sys_metadata
    if self.run_params['evals']:
      assert set(run.values.keys()) == set([
        '-'.join((data_name[1], metric_name)) for data_name, metric_name in itertools.product(
          self.run_params['evals'], self.run_params['params']['eval_metric']
        )
      ])
    assert not run.assignments
    assert not run.logs

  def test_wrong_dtrain_type(self):
    self.run_params = _form_random_run_params(task='regression')
    self.run_params['evals'] = numpy.random.random((5, 3))
    with pytest.raises(ValueError):
      sigopt.xgboost.run(**self.run_params)
