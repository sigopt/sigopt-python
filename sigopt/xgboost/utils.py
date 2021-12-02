import xgboost as xgb
import inspect
import json

def get_default_args(func):
  signature = inspect.signature(func)
  return {
    k: v.default
    for k, v in signature.parameters.items() if v.default is not inspect.Parameter.empty
  }

TRAIN_PARAMETERS = ['num_boost_round', 'early_stopping_rounds']

def get_train_defaults():
  train_default_args = get_default_args(xgb.train)
  defaults = {k: train_default_args[k] for k in TRAIN_PARAMETERS}
  return defaults

def parse_parameter(value):
  for t in (int, float, str):
    try:
      ret = t(value)
      return ret
    except ValueError:
      continue
  return str(value)


def get_booster_params(booster):
  # refer:
  # https://github.com/dmlc/xgboost/blob/406c70ba0e831babce4855d48793df6924e21cbf/python-package/xgboost/sklearn.py#L493

  '''Get xgboost specific parameters.'''
  config = json.loads(booster.save_config())
  stack = [config]
  internal = {}
  while stack:
    obj = stack.pop()
    for k, v in obj.items():
      if k.endswith('_param'):
        for p_k, p_v in v.items():
          internal[p_k] = p_v
      elif isinstance(v, dict):
        stack.append(v)

  params = {}
  for k, v in internal.items():
    params[k] = parse_parameter(v)

  return params

def get_train_params(**kwargs):
  params = get_train_defaults()
  for k, v in kwargs.items():
    if k in TRAIN_PARAMETERS:
      params[k] = v
  return params


def get_all_run_params(booster, **train_params):
  """
  Get all parameters of a run.

  Parameters
  ----------
  booster : xgboost.Booster
      Booster model.
  train_kwargs:
      Train args already set.

  Returns
  ----------
      dict of run parameters
  """
  params = get_train_params(**train_params)
  params.update(get_booster_params(booster))
  return params


def log_default_params(run, params, source='XGBoost Defaults', sort=40, default_show=False):
  reported = dict(run.params.items())
  params = {k:v if v is not None else 'None' for k, v in params.items() if k not in reported}
  run.set_parameters(params)
  run.set_parameters_sources_meta(source, sort, default_show)
  run.set_parameters_source(params, source)
