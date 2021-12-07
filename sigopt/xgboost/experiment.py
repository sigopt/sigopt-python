import copy

from .. import create_experiment
from .constants import (
  DEFAULT_BO_ITERATIONS,
  DEFAULT_CLASSIFICATION_METRIC,
  DEFAULT_EVALS_NAME,
  DEFAULT_NUM_BOOST_ROUND,
  DEFAULT_REGRESSION_METRIC,
  DEFAULT_SEARCH_PARAMS,
  METRICS_OPTIMIZATION_STRATEGY,
  PARAMETER_INFORMATION,
  SEARCH_BOUNDS,
  SUPPORTED_AUTOBOUND_PARAMS,
  SUPPORTED_METRICS_TO_OPTIMIZE,
)
from .run import parse_run_options
from .run import run as XGBRunWrapper


def check_if_bounds_in_limits(bounds, limits):  #TODO move to utils, don't want to deal with merge conflict atm
  min_limit_type = limits[0]
  max_limit_type = limits[-1]
  min_limit, max_limit = [float(f) for f in limits[1:-1].split(',')]
  IN_BOUNDS_MIN = min_limit < bounds['min'] if min_limit_type == '(' else min_limit <= bounds['min']
  IN_BOUNDS_MAX = max_limit > bounds['min'] if max_limit_type == ')' else max_limit >= bounds['min']
  return all([IN_BOUNDS_MIN, IN_BOUNDS_MAX])


class XGBExperiment:
  def __init__(self, experiment_config, dtrain, evals, params, num_boost_round, run_options):
    self.experiment_config_parsed = copy.deepcopy(experiment_config)
    self.dtrain = dtrain
    self.evals = evals
    self.params = params
    self.num_boost_round = num_boost_round
    self.run_options = run_options
    self.sigopt_experiment = None

  def parse_and_create_metrics(self):
    if 'metrics' in self.experiment_config_parsed and isinstance(self.experiment_config_parsed['metrics'], list):
      for metric in self.experiment_config_parsed['metrics']:
        if metric['strategy'] == 'optimize' and metric['name'] not in SUPPORTED_METRICS_TO_OPTIMIZE:
          raise ValueError(
            f"The chosen metric to optimize, {metric['name']}, is not supported."
          )

    else:
      if 'metrics' not in self.experiment_config_parsed:  # pick a default metric
        if 'objective' in self.params:
          objective = self.params['objective']
          if objective.split(':')[0] in ['binary', 'multi']:
            metric_to_optimize = DEFAULT_CLASSIFICATION_METRIC
          else:
            metric_to_optimize = DEFAULT_REGRESSION_METRIC  # do regression if anything else (including ranking)
        else:
          metric_to_optimize = DEFAULT_REGRESSION_METRIC
      else:
        if self.experiment_config_parsed['metrics'] not in SUPPORTED_METRICS_TO_OPTIMIZE:
          raise ValueError(
            f"The chosen metric to optimize, {self.experiment_config_parsed['metrics']}, is not supported."
          )
        metric_to_optimize = self.experiment_config_parsed['metrics']

      optimization_strategy = METRICS_OPTIMIZATION_STRATEGY[metric_to_optimize]
      self.experiment_config_parsed['metrics'] = [{
        'name': metric_to_optimize,
        'strategy': 'optimize',
        'objective': optimization_strategy
      }]

    # change optimized metric to reflect updated name
    for metric in self.experiment_config_parsed['metrics']:
      if metric['strategy'] == 'optimize':
        if isinstance(self.evals, list):
          metric['name'] = self.evals[0][1] + '-' + metric['name']  # optimize metric on first eval set by default
        else:
          metric['name'] = DEFAULT_EVALS_NAME + '-' + metric['name']

  def check_and_fill_parameter_types(self):
    params_to_check = [p for p in self.experiment_config_parsed['parameters'] if p['name'] in PARAMETER_INFORMATION]
    for parameter in params_to_check:
      parameter_name = parameter['name']
      if parameter_name in PARAMETER_INFORMATION:  # TODO: if parameter_name isn't here, probably should throw warning
        proper_parameter_type = PARAMETER_INFORMATION[parameter_name]['type']
        if 'type' in parameter:
          experiment_config_parameter_type = parameter['type']
          if experiment_config_parameter_type != proper_parameter_type:
            raise ValueError(f'Parameter {parameter_name} type listed incorrectly as {experiment_config_parameter_type}'
                             f'in experiment config, and should be listed as having type {proper_parameter_type}.')
        else:
          parameter['type'] = proper_parameter_type

  def check_and_fill_parameter_bounds(self):
    params_to_check = [p for p in self.experiment_config_parsed['parameters'] if p['name'] in PARAMETER_INFORMATION]
    for parameter in params_to_check:
      parameter_name = parameter['name']
      if 'bounds' not in parameter and PARAMETER_INFORMATION[parameter_name]['type'] in ['double', 'int']:
        if parameter_name not in SUPPORTED_AUTOBOUND_PARAMS:
          raise ValueError('We do not support autoselection of bounds for {param_name}.')
        search_bound = SEARCH_BOUNDS[SUPPORTED_AUTOBOUND_PARAMS.index(parameter_name)]
        parameter.update(search_bound)
      else:
        if parameter['type'] in ['double', 'int']:
          parameter_bounds = parameter['bounds']
          limits = PARAMETER_INFORMATION[parameter_name]['limits']
          if not check_if_bounds_in_limits(parameter_bounds, limits):
            raise ValueError(f'The min and max for {parameter_name} must be within the interval {limits}.')

        if parameter['type'] == 'categorical':
          proper_parameter_values = PARAMETER_INFORMATION[parameter_name]['values']
          config_parameter_values = parameter['categorical_values']
          if not set(proper_parameter_values) > set(config_parameter_values):
            raise ValueError(f'The set of possible categorical values {config_parameter_values} is not a subset of'
                             f'the permissible categorical values {proper_parameter_values}.')

  def parse_and_create_parameters(self):
    if 'parameters' not in self.experiment_config_parsed:
      self.experiment_config_parsed['parameters'] = [
        SEARCH_BOUNDS[SUPPORTED_AUTOBOUND_PARAMS.index(param_name)] for param_name in DEFAULT_SEARCH_PARAMS
      ]
    else:
      self.check_and_fill_parameter_types()
      self.check_and_fill_parameter_bounds()

    # Check key overlap between parameters to be optimized and parameters that are set
    params_optimized = [param['name'] for param in self.experiment_config_parsed['parameters']]
    params_overlap = set(params_optimized) & set(self.params.keys())
    if len(params_overlap) != 0:
      raise ValueError(
        f'There is overlap between tuned parameters and user-set parameters: {params_overlap}.'
        'Parameter names cannot be defined in both locations'
      )

    # Check that num_boost_round is not set by both sigopt experiment and user
    if self.num_boost_round and 'num_boost_round' in params_optimized:
      raise ValueError(
        'num_boost_round has been denoted as an optimization parameter, but also has been fixed in the input arguments'
        f'to have value {self.num_boost_round}. Please remove it from either the search space or the input arguments.'
      )

  def parse_and_create_experiment(self):
    self.parse_and_create_metrics()
    self.parse_and_create_parameters()
    if 'budget' not in self.experiment_config_parsed:
      self.experiment_config_parsed['budget'] = DEFAULT_BO_ITERATIONS
    if 'parallel_bandwidth' not in self.experiment_config_parsed:
      self.experiment_config_parsed['parallel_bandwidth'] = 1
    if 'type' not in self.experiment_config_parsed:
      self.experiment_config_parsed['type'] = 'offline'
    self.sigopt_experiment = create_experiment(**self.experiment_config_parsed)

  def run_experiment(self):
    for run in self.sigopt_experiment.loop():
      with run:
        if self.num_boost_round:
          num_boost_round_run = self.num_boost_round
        elif 'num_boost_round' in run.params:
          num_boost_round_run = run.params['num_boost_round']
        else:
          num_boost_round_run = DEFAULT_NUM_BOOST_ROUND
        all_params = {**run.params, **self.params, 'num_boost_round': num_boost_round_run}
        self.run_options['run'] = run

        XGBRunWrapper(
          all_params,
          self.dtrain,
          num_boost_round=num_boost_round_run,
          evals=self.evals,
          run_options=self.run_options
        )


def experiment(experiment_config, dtrain, evals, params, num_boost_round=None, run_options=None):
  run_options_parsed = parse_run_options(run_options)
  xgb_experiment = XGBExperiment(experiment_config, dtrain, evals, params, num_boost_round, run_options_parsed)
  xgb_experiment.parse_and_create_experiment()
  xgb_experiment.run_experiment()
  return xgb_experiment.sigopt_experiment
