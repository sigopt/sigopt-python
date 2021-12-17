import sigopt
from .compat import xgboost
from .run import run
import types

class ModeConfig:
  def __init__(self):
    self.run_options = None
    self.experiment_config = None
    self.mode = None

config = ModeConfig()

def wrap_f(f):
  def _f(*argv, **kwargs):
    return f(*argv, **kwargs)
  return _f

def wrap(obj):
  class Obj(object):
    pass
  new_obj = Obj()
  for att in dir(obj):
    v = getattr(obj, att)
    if not att.startswith('_') and isinstance(v, types.MethodType):
      setattr(new_obj, att, wrap_f(v))
  return new_obj

def xgboost_run(*argv, **kwargs):
  ctx = run(*argv, **kwargs)
  ctx.run.end()
  r = wrap(ctx.model)
  setattr(r, 'run', ctx.run)
  setattr(r, 'get_run', lambda : sigopt.get_run(ctx.run.id))
  return r

def xgboost_experiment(*argv, **kwargs):
  # TODO
  pass


saved_train = xgboost.train
def enable():
  xgboost._train = saved_train
  xgboost.train = new_xgboost_train

def disable():
  xgboost.train = saved_train

def set_mode(mode=None, run_options=None, experiment_config=None):
  config.mode = mode
  if mode == None:
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
