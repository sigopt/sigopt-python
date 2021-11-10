from .run import run as XGBRun
from .run import parse_run_options, PARAMS_LOGGED_AS_METADATA, DEFAULT_EVALS_NAME
from xgboost import DMatrix
import copy

from .. import create_experiment

DEFAULT_CLASSIFICATION_METRICS = ['accuracy', 'precision', 'recall', 'F1']
DEFAULT_REGRESSION_METRICS = ['mean absolute error', 'mean squared error']
DEFAULT_NUM_BOOST_ROUND = 10


class XGBExperiment:
  def __init__(self, experiment_config, dtrain, evals, params, num_boost_round, run_options):
    self.experiment_config = experiment_config
    self.dtrain = dtrain
    self.evals = evals
    self.params = params
    self.num_boost_round = num_boost_round
    self.run_options = run_options
    self.sigopt_experiment = None

  def parse_and_create_parameter_space(self):
    # TODO: deal with later
    pass

  def parse_and_create_experiment(self):
    experiment_config_parsed = copy.deepcopy(self.experiment_config)

    # Check experiment config optimization metric
    for metric in experiment_config_parsed['metrics']:
      if metric['strategy'] is 'optimize':
        assert metric['name'] in DEFAULT_CLASSIFICATION_METRICS or metric['name'] in DEFAULT_REGRESSION_METRICS

        # change optimized metric to reflect updated name
        metric['name'] = self.evals[0][1] + '-' + metric['name'] if isinstance(self.evals, list) else \
          DEFAULT_EVALS_NAME + '-' + metric['name']

    # Check key overlap between parameters to be optimized and parameters that are set
    params_optimized = [param['name'] for param in self.experiment_config['parameters']]
    assert len(set(params_optimized) & set(self.params.keys())) == 0, \
      'There is overlap between optimized params and user-set params'

    # Check that num_boost_round is not set by both sigopt experiment and user
    if self.num_boost_round:
      assert 'num_boost_round' not in params_optimized

    self.sigopt_experiment = create_experiment(**experiment_config_parsed)

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
        if not run.params.num_boost_round:
            run.params.update({'num_boost_round': num_boost_round_run})


        XGBRun(
          all_params, self.dtrain, num_boost_round=num_boost_round_run,
          evals=self.evals, run_options=self.run_options
        )


def experiment(experiment_config, dtrain, evals, params, num_boost_round=None, run_options=None):
  run_options_parsed = parse_run_options(run_options)
  xgb_experiment = XGBExperiment(experiment_config, dtrain, evals, params, num_boost_round, run_options_parsed)
  xgb_experiment.parse_and_create_parameter_space()
  xgb_experiment.parse_and_create_experiment()
  xgb_experiment.run_experiment()




