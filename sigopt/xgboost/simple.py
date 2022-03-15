import sigopt
from .compat import xgboost, xgboost_train
from .run import run
from .experiment import experiment


class ModeConfig:
  def __init__(self):
    self.run_options = None
    self.experiment_config = None
    self.mode = None

config = ModeConfig()

class WrapRun(object):
  def __init__(self, run, model):
    self.run = run
    self.model = model

  def get_run(self):
    return sigopt.get_run(self.run.id)

  def __getattr__(self, name):
    attrs = dir(self)
    if name in attrs:
      return attrs[name]
    return getattr(self.model, name)

class WrapExp(object):
  def __init__(self, experiment, model):
    self.experiment = experiment
    self.model = model

  def get_experiment(self):
    return sigopt.get_experiment(self.experiment.id)._experiment

  def __getattr__(self, name):
    attrs = dir(self)
    if name in attrs:
      return attrs[name]
    return getattr(self.model, name)


def xgboost_run(*argv, **kwargs):
  ctx = run(*argv, **kwargs)
  ctx.run.end()
  return WrapRun(ctx.run, ctx.model)

def xgboost_experiment(*argv, **kwargs):
  exp, runs = experiment(*argv, **kwargs, with_runs=True)
  best = list(exp.get_best_runs())[0]
  best_run = [run for run in runs if run.run.id == best.id][0]
  return WrapExp(exp, best_run.model)


def enable():
  xgboost.train = new_xgboost_train

def disable():
  xgboost.train = xgboost_train

def set_mode(mode='default', run_options=None, experiment_config=None):
  config.mode = mode
  if mode == 'default':
    disable()
  else:
    enable()
  config.run_options = run_options
  config.experiment_config = experiment_config

def new_xgboost_train(**kwargs):
  if config.mode == 'run':
    return xgboost_run(run_options=config.run_options, **kwargs)
  elif config.mode == 'experiment':
    return xgboost_experiment(
      experiment_config=config.experiment_config,
      run_options=config.run_options,
      **kwargs)
  else:
    return xgboost_train(**kwargs)
