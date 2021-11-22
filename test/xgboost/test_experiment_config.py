import pytest
import copy

from sklearn import datasets
from sklearn.model_selection import train_test_split
import xgboost as xgb
import numpy as np

from sigopt.xgboost.experiment import XGBExperiment

iris = datasets.load_iris()
X = iris.data
y = iris.target
num_class = 3
X_train, X_test, Y_train, Y_test = train_test_split(X, y, test_size=0.2)
D_train = xgb.DMatrix(X_train, label=Y_train)
D_test = xgb.DMatrix(X_test, label=Y_test)
EXPERIMENT_CONFIG_BASE = dict(
  name='Single metric optimization',
  type='offline',
  parameters=[
    dict(
      name='eta',
      type='double',
      bounds={'min': 0.1, 'max': 0.5}
    ),
    dict(
      name='max_depth',
      type='int',
      bounds={'min': 2, 'max': 6}
    ),
    dict(
      name='num_boost_round',
      type='int',
      bounds={'min': 2, 'max': 6}
    )
  ],
  metrics=[
    dict(
      name='accuracy',
      strategy='optimize',
      objective='maximize'
    )
  ],
  parallel_bandwidth=1,
  budget=2
)
params = {
  'num_class': num_class,
  'lambda': 1,
}


def verify_experiment_config_integrity(experiment_config):
  assert isinstance(experiment_config, dict)
  assert 'type' in experiment_config
  assert 'parameters' in experiment_config
  assert 'metrics' in experiment_config
  assert 'budget' in experiment_config

  parameters = experiment_config['parameters']
  for parameter in parameters:
    assert 'name' in parameter
    assert 'type' in parameter
    assert 'bounds' in parameter

  metrics = experiment_config['metrics']
  for metric in metrics:
    assert 'name' in metric
    assert 'strategy' in metric
    assert 'objective' in metric


class TestExperimentConfig:
  def verify_integrity(self, experiment_config):
    num_boost_round = None
    run_options = None
    xgb_experiment = XGBExperiment(experiment_config, D_train, D_test, params, num_boost_round, run_options)
    xgb_experiment.parse_and_create_metrics()
    xgb_experiment.parse_and_create_parameters()
    verify_experiment_config_integrity(xgb_experiment.experiment_config_parsed)

  def test_base(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    self.verify_integrity(experiment_config)

  def test_config_no_search_space(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    del experiment_config['parameters']
    self.verify_integrity(experiment_config)

  def test_config_search_space_string_only(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    for parameter in experiment_config['parameters']:
      del parameter['type']
      del parameter['bounds']
    self.verify_integrity(experiment_config)

  def test_config_search_space_mixed(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    del experiment_config['parameters'][2]['type']
    del experiment_config['parameters'][2]['bounds']
    self.verify_integrity(experiment_config)

  def test_config_metric_string(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    del experiment_config['metrics']
    experiment_config['metrics'] = 'accuracy'
    self.verify_integrity(experiment_config)

  def test_config_metric_list(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    experiment_config['metrics'].append(dict(
      name='f1',
      strategy='store',
      objective='maximize'
    ))
    self.verify_integrity(experiment_config)
