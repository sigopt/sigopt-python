import copy
from mock import Mock
import pytest

from sigopt.xgboost.constants import (
  DEFAULT_CLASSIFICATION_METRIC,
  DEFAULT_EVALS_NAME,
  DEFAULT_REGRESSION_METRIC,
  PARAMETER_INFORMATION,
  SUPPORTED_AUTOBOUND_PARAMS,
)
from sigopt.xgboost.experiment import XGBExperiment

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
PARAMS_BASE = {
  'num_class': 3,
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
    if parameter['type'] in ['int', 'double']:
      assert 'bounds' in parameter
    if parameter['type'] == 'categorical':
      assert 'categorical_values' in parameter

  metrics = experiment_config['metrics']
  for metric in metrics:
    assert 'name' in metric
    assert 'strategy' in metric
    assert 'objective' in metric


def parse_and_create_experiment_config(experiment_config, params):
  num_boost_round = None
  run_options = None
  d_train = Mock()
  evals = Mock()
  xgb_experiment = XGBExperiment(experiment_config, d_train, evals, params, num_boost_round, run_options)
  xgb_experiment.parse_and_create_metrics()
  xgb_experiment.parse_and_create_parameters()
  return xgb_experiment


class TestExperimentConfig:
  def verify_integrity(self, experiment_config, params):
    xgb_experiment = parse_and_create_experiment_config(experiment_config, params)
    verify_experiment_config_integrity(xgb_experiment.experiment_config_parsed)

  def test_check_supported_params(self):
    assert set(PARAMETER_INFORMATION.keys()) > set(SUPPORTED_AUTOBOUND_PARAMS)

  def test_base(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    params = copy.deepcopy(PARAMS_BASE)
    self.verify_integrity(experiment_config, params)

  def test_config_no_search_space(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    params = copy.deepcopy(PARAMS_BASE)
    del experiment_config['parameters']
    self.verify_integrity(experiment_config, params)

  def test_config_search_space_name_only(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    params = copy.deepcopy(PARAMS_BASE)
    for parameter in experiment_config['parameters']:
      del parameter['type']
      del parameter['bounds']
    self.verify_integrity(experiment_config, params)

  def test_config_detect_log_transformation(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    params = copy.deepcopy(PARAMS_BASE)
    experiment_config['parameters'] = [dict(name='eta')]
    xgb_experiment = parse_and_create_experiment_config(experiment_config, params)
    assert xgb_experiment.experiment_config_parsed['parameters'][0]['transformation'] == 'log'

  def test_config_search_space_mixed(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    params = copy.deepcopy(PARAMS_BASE)
    del experiment_config['parameters'][2]['type']
    del experiment_config['parameters'][2]['bounds']
    self.verify_integrity(experiment_config, params)

  def test_config_search_space_wrong_type(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    params = copy.deepcopy(PARAMS_BASE)
    experiment_config['parameters'][0]['type'] = 'int'
    del experiment_config['parameters'][0]['bounds']
    with pytest.raises(ValueError):
      self.verify_integrity(experiment_config, params)

  def test_config_search_space_no_type(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    params = copy.deepcopy(PARAMS_BASE)
    del experiment_config['parameters'][0]['type']
    del experiment_config['parameters'][1]['type']
    del experiment_config['parameters'][2]['type']
    self.verify_integrity(experiment_config, params)

  def test_config_search_space_categories_no_type(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    params = copy.deepcopy(PARAMS_BASE)
    experiment_config['parameters'].append(
      dict(
        name='tree_method',
        categorical_values=['auto', 'exact', 'hist', 'gpu_hist'],
      )
    )
    self.verify_integrity(experiment_config, params)

  def test_config_search_space_wrong_categories(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    params = copy.deepcopy(PARAMS_BASE)
    experiment_config['parameters'].append(
      dict(
        name='tree_method',
        type='categorical',
        categorical_values=['auto', 'exact', 'hist', 'gpu_hist', 'WrongCategory'],
      )
    )
    with pytest.raises(ValueError):
      self.verify_integrity(experiment_config, params)

  def test_config_search_space_fake_categories(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    params = copy.deepcopy(PARAMS_BASE)
    experiment_config['parameters'].append(
      dict(
        name='foo',
        type='categorical',
        categorical_values=['auto', 'exact', 'hist', 'gpu_hist', 'WrongCategory'],
      )
    )
    self.verify_integrity(experiment_config, params)

  def test_config_search_space_wrong_bounds(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    params = copy.deepcopy(PARAMS_BASE)
    experiment_config['parameters'][0]['bounds'] = {'min': -0.1, 'max': 5.0}
    with pytest.raises(ValueError):
      self.verify_integrity(experiment_config, params)

  def test_config_no_supported_bounds(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    experiment_config['parameters'].append(dict(name='max_leaves'))
    params = copy.deepcopy(PARAMS_BASE)
    with pytest.raises(ValueError):
      self.verify_integrity(experiment_config, params)

  def test_autodetect_metric_from_objective(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    del experiment_config['metrics']
    params = copy.deepcopy(PARAMS_BASE)

    params['objective'] = 'binary:logistic'
    xgb_experiment = parse_and_create_experiment_config(experiment_config, params)
    assert xgb_experiment.experiment_config_parsed['metrics'][0]['name'] == '-'.join(
      (DEFAULT_EVALS_NAME, DEFAULT_CLASSIFICATION_METRIC)
    )

    params['objective'] = 'multi:softmax'
    xgb_experiment = parse_and_create_experiment_config(experiment_config, params)
    assert xgb_experiment.experiment_config_parsed['metrics'][0]['name'] == '-'.join(
      (DEFAULT_EVALS_NAME, DEFAULT_CLASSIFICATION_METRIC)
    )

    params['objective'] = 'reg:squarederror'
    xgb_experiment = parse_and_create_experiment_config(experiment_config, params)
    assert xgb_experiment.experiment_config_parsed['metrics'][0]['name'] == '-'.join(
      (DEFAULT_EVALS_NAME, DEFAULT_REGRESSION_METRIC)
    )

  def test_config_metric_string_only(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    params = copy.deepcopy(PARAMS_BASE)
    experiment_config['metrics'] = 'accuracy'
    self.verify_integrity(experiment_config, params)

  def test_config_metric_list(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    experiment_config['metrics'].append(dict(
      name='f1',
      strategy='store',
      objective='maximize'
    ))
    params = copy.deepcopy(PARAMS_BASE)
    self.verify_integrity(experiment_config, params)

  def test_config_param_defined_twice(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    params = copy.deepcopy(PARAMS_BASE)
    params['eta'] = 0.1
    with pytest.raises(ValueError):
      self.verify_integrity(experiment_config, params)

  def test_config_num_boost_round_defined_twice(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    params = copy.deepcopy(PARAMS_BASE)
    params['num_boost_round'] = 10
    with pytest.raises(ValueError):
      self.verify_integrity(experiment_config, params)

  def test_config_wrong_metric_string(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    experiment_config['metrics'] = 'NOT_A_METRIC_SUPPORTED'
    params = copy.deepcopy(PARAMS_BASE)
    with pytest.raises(ValueError):
      self.verify_integrity(experiment_config, params)

  def test_config_wrong_metric_list(self):
    experiment_config = copy.deepcopy(EXPERIMENT_CONFIG_BASE)
    experiment_config['metrics'][0]['name'] = 'NOT_A_METRIC_SUPPORTED'
    params = copy.deepcopy(PARAMS_BASE)
    with pytest.raises(ValueError):
      self.verify_integrity(experiment_config, params)

