import copy
import pytest
import random

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
    if not any([p['name'] in ['eta', 'min_child_weight'] for p in search_space]):
       search_space.append(SEARCH_SPACES[0])
    return search_space

  def _form_random_experiment_config(self, task):
    experiment_params = _form_random_run_params(task)
    is_classification = True if task in ('binary', 'multiclass') else False
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
      'name': 'Integration test',
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

  @pytest.mark.parametrize('task', ['binary', 'multiclass', 'regression'])
  def test_experiment(self, task):
    self._form_random_experiment_config(task)
    experiment = sigopt.xgboost.experiment(**self.experiment_params)
    assert experiment.is_finished()
