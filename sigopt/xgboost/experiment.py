from .run import run as XGBRun
from .run import DEFAULT_RUN_OPTIONS, parse_run_options, PARAMS_LOGGED_AS_METADATA, DEFAULT_EVALS_NAME

from .. import create_experiment

def experiment(experiment_config, dtrain, evals, params, num_boost_round=10, run_options=None):

  # Check consistency between logged metric in config and what will actually be logged in run

  experiment = create_experiment(**experiment_config)
  for run in experiment.loop():
    with run:

      # Check key overlap between parameters to be optimized and parameters that are set
      assert len(set(run.params.keys()) & set(params.keys())) == 0, \
        'There is overlap between optimized params and user-set params'

      all_params = {**run.params, **params, 'num_boost_round': num_boost_round}
      run_options = {}
      run_options['run'] = run

      # Separately log params that aren't experiment params
      run_options['log_params'] = False
      for name in params.keys():
        if name not in PARAMS_LOGGED_AS_METADATA:
          run.params.update({name: params[name]})
      run.params.num_boost_round = num_boost_round

      XGBRun(all_params, dtrain, num_boost_round=num_boost_round, evals=evals, run_options=run_options)
