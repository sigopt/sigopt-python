import platform
import random
import pytest
import copy

import sigopt.xgboost
from sigopt.xgboost.run import PARAMS_LOGGED_AS_METADATA
from sklearn import datasets
from sklearn.model_selection import train_test_split
import xgboost as xgb
import numpy as np



from .test_xgboost import (
  TestXGBoost
)

SEARCH_SPACES = [
  {
      'name': 'eta',
      'type': 'double',
      'bounds': {'min': 0.1, 'max': 0.5}
  },
  {
    'name': 'min_child_weight',
    'type': 'double',
    'bounds': {'min': 0.0, 'max': 0.3}
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

from sigopt.xgboost.experiment import DEFAULT_CLASSIFICATION_METRICS, DEFAULT_REGRESSION_METRICS

class TestXGBoostExperiment(TestXGBoost):
  def _form_random_experiment_config(self):
    metric_to_optimize = random.choice(DEFAULT_CLASSIFICATION_METRICS) if self.is_classification \
      else random.choice(DEFAULT_REGRESSION_METRICS)
    random_subset_size = random.randint(1, len(SEARCH_SPACES))
    self.search_space = random.sample(SEARCH_SPACES, random_subset_size)
    for param in self.search_space:
      self.run_params['params'].pop(param['name'], None)
    experiment_config = {
      'name': 'Integration test',
      'type': 'offline',
      'parameters': self.search_space,
      'metrics': {
        'name': metric_to_optimize,
        'strategy': 'optimize',
        'objective': 'maximize'
      },
      'parallel_bandwidth': 1,
      'budget': random.randint(1, 8)
    }
    self.experiment_params = self.run_params
    self.experiment_params['experiment_config'] = experiment_config
    del self.experiment_params['verbose_eval']

  @pytest.mark.parametrize('task', ['binary', 'multiclass', 'regression'])
  def test_experiment(self, task):
    self._form_random_run_params(task)
    self._form_random_experiment_config()
    experiment = sigopt.xgboost.experiment(**self.experiment_params)
    assert experiment.is_finished()

  def test_run(self, task):
    pass