from .run import run as XGBRun
from .run import parse_run_options, PARAMS_LOGGED_AS_METADATA, DEFAULT_EVALS_NAME
import copy

from .. import create_experiment
from .constants import (
  DEFAULT_BO_ITERATIONS,
  DEFAULT_CLASSIFICATION_METRIC,
  DEFAULT_NUM_BOOST_ROUND,
  DEFAULT_REGRESSION_METRIC,
  DEFAULT_SEARCH_PARAMS,
  SEARCH_BOUNDS,
  SEARCH_PARAMS,
  SUPPORTED_METRICS_TO_OPTIMIZE,
  METRICS_OPTIMIZATION_STRATEGY,
)


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

  def parse_and_create_parameters(self):
    if 'parameters' not in self.experiment_config_parsed:
      self.experiment_config_parsed['parameters'] = [
        SEARCH_BOUNDS[SEARCH_PARAMS.index(param_name)] for param_name in DEFAULT_SEARCH_PARAMS
      ]
    else:
      for param in self.experiment_config_parsed['parameters']:
        if 'bounds' not in param:
          param_name = param['name']
          if param_name not in SEARCH_PARAMS:
            raise ValueError('We do not support autoselection of bounds for {param_name}')
          search_bound = SEARCH_BOUNDS[SEARCH_PARAMS.index(param_name)]
          param.update(search_bound)

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

        # Separately log params that aren't experiment params TODO: change when param sources is good to go
        self.run_options['log_params'] = False
        for name in self.params.keys():
          if name not in PARAMS_LOGGED_AS_METADATA:
            run.params.update({name: self.params[name]})
        if 'num_boost_round' not in run.params:
          run.params.update({'num_boost_round': num_boost_round_run})

        XGBRun(
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
