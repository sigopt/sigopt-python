# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import copy
import os
import pytest
import random

os.environ['SIGOPT_PROJECT'] = "dev-sigopt-xgb-integration-test"

import sigopt.xgboost
from sigopt.xgboost.constants import CLASSIFICATION_METRIC_CHOICES, REGRESSION_METRIC_CHOICES
from .test_xgboost_run import _form_random_run_params

SEARCH_SPACES = [
  {
    'name': 'eta',
  },
  {
    'name': 'min_child_weight',
  },
  {
    'name': 'max_depth',
    'type': 'int',
    'bounds': {'min': 2, 'max': 5}
  },
  {
    'name': 'num_boost_round',
    'type': 'int',
    'bounds': {'min': 2, 'max': 5}
  },
]


class TestXGBoostExperiment:
  experiment_params = None

  def _generate_randomized_search_space(self):
    search_space = copy.deepcopy(SEARCH_SPACES)
    if random.randint(0, 1) == 1:  # add bounds and type to eta randomly
      search_space[0]['type'] = 'double'
      search_space[0]['bounds'] = {'min': 0.1, 'max': 0.5}
    if random.randint(0, 1) == 1:   # add bounds and type to min_child_weight randomly
      search_space[1]['type'] = 'double'
      search_space[1]['bounds'] = {'min': 0.0, 'max': 0.3}
    random_subset_size = random.randint(1, len(search_space))
    search_space = random.sample(search_space, random_subset_size)
    if not any(p['name'] in ['eta', 'min_child_weight'] for p in search_space):
      search_space.append(SEARCH_SPACES[0])
    return search_space

  def _form_random_experiment_config(self, task):
    experiment_params = _form_random_run_params(task)
    is_classification = bool(task in ('binary', 'multiclass'))
    if is_classification:
      metric_to_optimize = random.choice(CLASSIFICATION_METRIC_CHOICES)
    else:
      metric_to_optimize = random.choice(REGRESSION_METRIC_CHOICES)
    search_space = self._generate_randomized_search_space()

    for param in search_space:
      experiment_params['params'].pop(param['name'], None)
      if param['name'] == 'num_boost_round':
        experiment_params.pop('num_boost_round', None)

    experiment_config = {
      'name': f"xgboost-experiment-integration-test-{task}",
      'type': 'offline',
      'parameters': search_space,
      'metrics': [{
        'name': metric_to_optimize,
        'strategy': 'optimize',
        'objective': 'maximize'
      }],
      'parallel_bandwidth': 1,
      'budget': random.randint(1, 3)
    }
    if random.randint(0, 1) == 0:
      del experiment_config['metrics']

    experiment_params['experiment_config'] = experiment_config
    experiment_params['run_options'].pop('name', None)
    experiment_params.pop('verbose_eval', None)
    self.experiment_params = experiment_params

  def _verify_parameter_assignments_for_all_runs(self, all_runs, parameters_list):
    for ssr in all_runs:
      for param in parameters_list:
        if param.type in ('double', 'int'):
          assert param.bounds.min <= ssr.assignments[param.name] <= param.bounds.max
        else:
          categories = [c.name for c in param.categorical_values]
          assert ssr.assignments[param.name] in categories

  def _verify_metrics_for_all_runs(self, all_runs, metrics_list):
    for ssr in all_runs:
      if ssr.state != 'failed':
        for metric in metrics_list:
          assert ssr.values[metric.name]

  @pytest.mark.parametrize('task', ['binary', 'multiclass', 'regression'])
  def test_experiment(self, task):
    self._form_random_experiment_config(task)
    experiment = sigopt.xgboost.experiment(**self.experiment_params) #pylint: disable=unexpected-keyword-arg
    assert experiment.is_finished()
    sigopt_suggested_runs = list(experiment.get_runs())
    assert len(sigopt_suggested_runs) == self.experiment_params['experiment_config']['budget']
    self._verify_parameter_assignments_for_all_runs(sigopt_suggested_runs, experiment.parameters)
    self._verify_metrics_for_all_runs(sigopt_suggested_runs, experiment.metrics)
    experiment.archive()

  def test_early_stopping(self):
    self._form_random_experiment_config('binary')
    self.experiment_params['early_stopping_rounds'] = 1
    experiment = sigopt.xgboost.experiment(**self.experiment_params) #pylint: disable=unexpected-keyword-arg
    assert experiment.is_finished()
    sigopt_suggested_runs = list(experiment.get_runs())
    for ssr in sigopt_suggested_runs:
      assert ssr.assignments['early_stopping_rounds'] == self.experiment_params['early_stopping_rounds']
      assert ssr.values['num_boost_round_before_stopping'].value >= 0
    experiment.archive()

  def test_experiment_with_custom_loop(self):
    run_params = _form_random_run_params('binary')
    if len(run_params['evals']) > 1:
      run_params['evals'] = run_params['evals'][:1]

    fixed_params = {
      'alpha': 0.2,
      'objective': 'binary:logistic',
      'eval_metric': ['logloss', 'auc'],
    }
    experiment_config=dict(
      name="xgboost a la carte",
      type="offline",
      parameters=[
        dict(name="eta", type="double", bounds=dict(min=1e-4, max=10), transformation='log'),
        dict(name="num_boost_round", type="int", bounds=dict(min=10, max=50)),
        dict(name="booster", type="categorical", categorical_values=(['gbtree', 'gblinear'])),
      ],
      metrics=[
        dict(name="test0-F1"),
        dict(name="Training time", strategy="optimize", objective="minimize"),
        dict(name="test0-recall", strategy="store", objective="maximize"),
      ],
      budget=5,
    )
    experiment = sigopt.create_aiexperiment(**experiment_config)
    custom_run = experiment.create_run()

    ctx = sigopt.xgboost.run(
      params=fixed_params,
      dtrain=run_params['dtrain'],
      evals=run_params['evals'],
      verbose_eval=False,
      run_options={'run': custom_run},
    )

    run_obj = sigopt.get_run(ctx.run.id)
    assert run_obj.assignments['alpha'] == fixed_params['alpha']
    assert run_obj.metadata['objective'] == fixed_params['objective']
    assert run_obj.metadata['eval_metric'] == str(fixed_params['eval_metric'])
    assert run_obj.assignments['eta']  == custom_run.params['eta']
    assert run_obj.assignments['num_boost_round'] == custom_run.params['num_boost_round']
    assert run_obj.assignments['booster'] in ('gbtree', 'gblinear')
    assert 0 <= run_obj.values['test0-F1'].value <= 1
    assert 0 <= run_obj.values['test0-recall'].value <= 1
    assert run_obj.values['Training time'].value > 0
    self._verify_parameter_assignments_for_all_runs([run_obj], experiment.parameters)
    self._verify_metrics_for_all_runs([run_obj], experiment.metrics)
    ctx.run.end()
    assert not experiment.is_finished()
    assert len(list(experiment.get_runs())) == 1
    experiment.archive()
