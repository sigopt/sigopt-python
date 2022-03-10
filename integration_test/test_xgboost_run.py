from inspect import signature
import itertools
import json
import os
import platform
import pytest
import random

os.environ['SIGOPT_PROJECT'] = "dev-sigopt-xgb-integration-test"

import numpy
import sigopt.xgboost
from sigopt.xgboost.checkpoint_callback import SigOptCheckpointCallback
from sigopt.xgboost.constants import (
  CLASSIFICATION_METRIC_CHOICES,
  DEFAULT_EVALS_NAME,
  REGRESSION_METRIC_CHOICES,
)
from sigopt.xgboost.run import (
  DEFAULT_CHECKPOINT_PERIOD,
  PARAMS_LOGGED_AS_METADATA,
  XGB_INTEGRATION_KEYWORD,
  XGBRunHandler,
)
from sklearn import datasets
from sklearn.model_selection import train_test_split
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

  run_params =  dict(
    params=subset_params,
    dtrain=D_train,
    evals=[(D_test, f'test{n}') for n in range(random.randint(1, 3))],
    num_boost_round=random.randint(3, 15),
    verbose_eval=random.choice([True, False]),
    run_options=run_options,
  )
  if numpy.random.rand() > 0.5:
    run_params['early_stopping_rounds'] = 10
  return run_params
#
class TestXGBoostRun(object):
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
    data_names = []
    if self.run_params['evals']:
      data_names.extend([e[-1] for e in self.run_params['evals']])
    if self.is_classification:
      for d_name, m_name in itertools.product(data_names, CLASSIFICATION_METRIC_CHOICES):
        assert 0 <= run.values['-'.join((d_name, m_name))].value <= 1
    else:
      for d_name, m_name in itertools.product(data_names, REGRESSION_METRIC_CHOICES):
        assert run.values['-'.join((d_name, m_name))].value >= 0

    if self.run_params['params']['eval_metric']:
      for d_name, m_name in itertools.product(data_names[1:], self.run_params['params']['eval_metric']):
        assert run.values['-'.join((d_name, m_name))]

    assert run.values['Training time'].value > 0
    assert run.values['best_iteration'].value >= 0
    if 'early_stopping_rounds' in self.run_params:
      assert run.values['num_boost_round_before_stopping'].value > 0


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
        assert set(run.datasets) == {e[1] for e in self.run_params['evals']}
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
    self.is_classification = bool(task in ('binary', 'multiclass'))
    self.run_params = _form_random_run_params(task)
    ctx = sigopt.xgboost.run(**self.run_params)
    run = sigopt.get_run(ctx.run.id)

    self._verify_metadata_logging(run)
    self._verify_parameter_logging(run)
    self._verify_metric_logging(run)
    self._verify_feature_importances_logging(run, ctx.model)
    self._verify_miscs_data_logging(run)
    ctx.run.end()

  def test_run_options_no_logging(self):
    self.run_params = _form_random_run_params(task='binary')
    self.run_params['run_options'].update({
      'autolog_checkpoints': False,
      'autolog_feature_importances': False,
      'autolog_metrics': False,
      'autolog_stderr': False,
      'autolog_stdout': False,
      'autolog_xgboost_defaults': False,
    })
    if 'early_stopping_rounds' in self.run_params:
      del self.run_params['early_stopping_rounds']
    ctx = sigopt.xgboost.run(**self.run_params)
    run = sigopt.get_run(ctx.run.id)

    assert run.checkpoint_count == 0
    assert 'feature_importances' not in run.sys_metadata
    if self.run_params['evals']:
      assert set(run.values.keys()) == {
        '-'.join((data_name[1], metric_name)) for data_name, metric_name in itertools.product(
          self.run_params['evals'], self.run_params['params']['eval_metric']
        )
      }
    assert len(run.assignments) <= len(self.run_params['params']) + 1
    self._verify_miscs_data_logging(run)
    assert not run.logs
    ctx.run.end()

  def test_wrong_dtrain_type(self):
    self.run_params = _form_random_run_params(task='regression')
    self.run_params['evals'] = numpy.random.random((5, 3))
    with pytest.raises(TypeError):
      sigopt.xgboost.run(**self.run_params)

  def test_log_default_params(self):
    self.run_params = _form_random_run_params(task="multiclass")
    self.run_params['params'] = POSSIBLE_PARAMETERS.copy()
    del self.run_params['params']['eta']
    del self.run_params['params']['gamma']
    del self.run_params['params']['lambda']
    del self.run_params['num_boost_round']
    ctx = sigopt.xgboost.run(**self.run_params)
    run = sigopt.get_run(ctx.run.id)
    assert numpy.isclose(run.assignments['eta'], 0.3)
    assert run.assignments['gamma'] == 0
    assert run.assignments['lambda'] == 1
    assert run.assignments['num_boost_round'] == 10

  def test_provided_run(self):
    self.run_params = _form_random_run_params(task="binary")
    run = sigopt.create_run(name="placeholder-run-with-max-depth-already-logged")
    run.params.update({'max_depth': 3})
    run.params.update({'num_boost_round': 7})

    self.run_params['run_options'].update({
      'autolog_checkpoints': False,
      'autolog_feature_importances': False,
      'autolog_metrics': False,
      'autolog_stderr': False,
      'autolog_stdout': False,
      'run': run,
      'name': None,
    })
    self.run_params['params'] = {'max_depth': 9}
    del self.run_params['num_boost_round']
    ctx = sigopt.xgboost.run(**self.run_params)
    booster = ctx.model
    params = json.loads(booster.save_config())
    trained_max_depth = params['learner']['gradient_booster']['updater']['grow_colmaker']['train_param']['max_depth']
    assert int(trained_max_depth) == 3
    bst_jsons = booster.get_dump(dump_format='json')
    assert len(bst_jsons) == 7
    run = sigopt.get_run(ctx.run.id)
    assert run.assignments['max_depth'] == 3
    assert run.assignments['num_boost_round'] == 7
    ctx.run.end()


class TestFormCallbacks(object):
  def _append_xgbrun_param_none_values(self):
    all_xgbrun_params_names = signature(XGBRunHandler).parameters.keys()
    for p_name in all_xgbrun_params_names:
      if p_name not in self.run_params:
        self.run_params[p_name] = None

  @pytest.mark.parametrize("verbose_eval", [True, False, 1, 3, 23])
  def test_xgbrun_form_callbacks(self, verbose_eval):
    self.run_params = _form_random_run_params(task="multiclass")
    self.run_params['verbose_eval'] = verbose_eval
    self.run_params['num_boost_round'] = 35
    self.run_params['callbacks'] = None
    self._append_xgbrun_param_none_values()
    xgbrun = XGBRunHandler(**self.run_params)
    xgbrun.form_callbacks()
    assert len(xgbrun.callbacks) == 1
    callback = xgbrun.callbacks[0]
    assert isinstance(callback, SigOptCheckpointCallback)
    if verbose_eval is False:
      assert callback.period == DEFAULT_CHECKPOINT_PERIOD
    else:
      assert callback.period == int(verbose_eval)

  def test_xgbrun_checkpoint_period_high_num_boost_round(self):
    self.run_params = _form_random_run_params(task="multiclass")
    self.run_params['verbose_eval'] = False
    self.run_params['num_boost_round'] = 200
    self.run_params['callbacks'] = None
    self._append_xgbrun_param_none_values()
    xgbrun = XGBRunHandler(**self.run_params)
    xgbrun.form_callbacks()
    assert len(xgbrun.callbacks) == 1
    callback = xgbrun.callbacks[0]
    assert callback.period == DEFAULT_CHECKPOINT_PERIOD

    self.run_params['verbose_eval'] = True
    self.run_params['num_boost_round'] = 999
    xgbrun = XGBRunHandler(**self.run_params)
    xgbrun.form_callbacks()
    callback = xgbrun.callbacks[0]
    assert callback.period == DEFAULT_CHECKPOINT_PERIOD

    self.run_params['num_boost_round'] = 1000
    xgbrun = XGBRunHandler(**self.run_params)
    xgbrun.form_callbacks()
    callback = xgbrun.callbacks[0]
    assert callback.period == 6

    self.run_params['num_boost_round'] = 3000
    xgbrun = XGBRunHandler(**self.run_params)
    xgbrun.form_callbacks()
    callback = xgbrun.callbacks[0]
    assert callback.period == 16

  def test_xgbrun_callbacks_appending(self):
    self.run_params = _form_random_run_params(task="multiclass")
    self.run_params['verbose_eval'] = False
    self.run_params['callbacks'] = [xgb.callback.EvaluationMonitor(period=3)]
    self._append_xgbrun_param_none_values()
    xgbrun = XGBRunHandler(**self.run_params)
    xgbrun.form_callbacks()
    assert len(xgbrun.callbacks) == 2
    assert xgbrun.callbacks[0].period == xgbrun.callbacks[1].period

  def test_xgbrun_callbacks_no_appending(self):
    self.run_params = _form_random_run_params(task="multiclass")
    self.run_params['callbacks'] = [xgb.callback.EarlyStopping(rounds=3)]
    self.run_params['evals'] = None
    self._append_xgbrun_param_none_values()
    xgbrun = XGBRunHandler(**self.run_params)
    xgbrun.form_callbacks()
    assert len(xgbrun.callbacks) == 1
    assert isinstance(xgbrun.callbacks[0], xgb.callback.EarlyStopping)

  def test_xgbrun_did_early_stop(self):
    """
    This test is slightly more involved, and uses a dataset and params for which we know XGB will early stop, and
    then verifies that early stopping occurs
    """
    d = 10
    n = 500
    numpy.random.seed(1234)
    X = numpy.random.rand(n, d)
    y = numpy.zeros(n)
    y[0:10] = 1
    X_train, X_test, Y_train, Y_test = train_test_split(X, y, test_size=0.2, random_state=1234)
    D_train = xgb.DMatrix(X_train, label=Y_train)
    D_test = xgb.DMatrix(X_test, label=Y_test)
    self.run_params = _form_random_run_params(task="binary")
    self.run_params['dtrain'] = D_train
    self.run_params['evals'] = D_test
    self.run_params['num_boost_round'] = 100
    self.run_params['early_stopping_rounds'] = 2
    ctx = sigopt.xgboost.run(**self.run_params)
    run = sigopt.get_run(ctx.run.id)
    assert run.values['num_boost_round_before_stopping'].value < self.run_params['num_boost_round']
