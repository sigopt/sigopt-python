import copy
import math
import json
import platform
import time

from .. import create_run
from ..context import Context
from ..log_capture import SystemOutputStreamMonitor
from ..run_context import RunContext
from .checkpoint_callback import SigOptCheckpointCallback
from .compat import DMatrix, xgboost
from .compute_metrics import compute_classification_metrics, compute_regression_metrics
from .utils import get_all_run_params


DEFAULT_EVALS_NAME = 'TestSet'
DEFAULT_TRAINING_NAME = 'TrainingSet'

XGBOOST_DEFAULTS_SOURCE = 'XGBoost Defaults'

DEFAULT_RUN_OPTIONS = {
  'log_checkpoints': True,
  'log_feature_importances': True,
  'log_metrics': True,
  'log_params': True,
  'log_stdout': True,
  'log_stderr': True,
  'log_sys_info': True,
  'name': None,
  'run': None,
}
DEFAULT_CHECKPOINT_PERIOD = 5
MAX_NUM_CHECKPOINTS = 200
FEATURE_IMPORTANCES_MAX_NUM_FEATURE = 50
XGB_INTEGRATION_KEYWORD = '_IS_XGB_RUN'

PARAMS_LOGGED_AS_METADATA = [
  'eval_metric',
  'objective',
  'updater',
]
SUPPORTED_OBJECTIVE_PREFIXES = [
  'binary',
  'multi',
  'reg',
]


def parse_run_options(run_options):
  if run_options is not None:
    if not isinstance(run_options, dict):
      # TODO(Harvey): change to actual doc url when it's online
      doc_url = "https://app.sigopt.com/docs/intro/overview"
      raise TypeError(
        f"run_options should be a dictonary. Refer to the sigopt.xgboost.run documentation {doc_url}"
      )

    if run_options.keys() - DEFAULT_RUN_OPTIONS.keys():
      raise ValueError(
        f"Unsupported keys {run_options.keys() - DEFAULT_RUN_OPTIONS.keys()} in run_options."
      )

    if {'run', 'name'}.issubset(run_options.keys()):
      if run_options['run'] and run_options['name']:
        raise ValueError(
          "Cannot speicify both `run` and `name` keys inside run_options."
        )

    if 'run' in run_options.keys() and run_options['run'] is not None:
      if not isinstance(run_options['run'], RunContext):
        raise TypeError(
          "`run` must be an instance of RunContext object, not {type(run_options['run']).__name__}."
        )

    return {**DEFAULT_RUN_OPTIONS, **run_options}

  return copy.deepcopy(DEFAULT_RUN_OPTIONS)


class XGBRun:

  def __init__(
    self,
    params,
    dtrain,
    num_boost_round,
    obj,
    feval,
    maximize,
    evals,
    early_stopping_rounds,
    evals_result,
    verbose_eval,
    xgb_model,
    callbacks,
    run_options,
  ):
    self.params = params
    self.dtrain = dtrain
    self.num_boost_round = num_boost_round
    self.obj = obj
    self.feval = feval
    self.maximize = maximize
    self.early_stopping_rounds = early_stopping_rounds
    self.verbose_eval = verbose_eval
    self.callbacks = callbacks
    self.validation_sets = [(evals, DEFAULT_EVALS_NAME)] if isinstance(evals, DMatrix) else evals
    self.evals_result = evals_result
    self.run_options_parsed = parse_run_options(run_options)
    self.run = None
    self.model = xgb_model
    self.is_regression = None

  def form_callbacks(self):
    # if no validation set, checkpointing not possible
    if not (self.run_options_parsed['log_checkpoints'] and self.validation_sets):
      return

    if self.callbacks is None:
      self.callbacks = []
    period = DEFAULT_CHECKPOINT_PERIOD
    if self.callbacks:
      for cb in self.callbacks:
        if isinstance(cb, xgboost.callback.EvaluationMonitor):
          period = cb.period
    if self.verbose_eval:
      period = 1 if self.verbose_eval is True else self.verbose_eval
    period = max(period, math.ceil((self.num_boost_round + 1) / MAX_NUM_CHECKPOINTS))
    sigopt_checkpoint_callback = SigOptCheckpointCallback(self.run, period=period)
    self.callbacks.append(sigopt_checkpoint_callback)

  def make_run(self):
    if self.run_options_parsed['run'] is not None:
      self.run = self.run_options_parsed['run']
    elif self.run_options_parsed['name'] is not None:
      self.run = create_run(name=self.run_options_parsed['name'])
    else:
      self.run = create_run()

  def log_metadata(self):
    self.run.log_dev_metadata(XGB_INTEGRATION_KEYWORD, True)

    if self.run_options_parsed['log_sys_info']:
      python_version = platform.python_version()
      self.run.log_metadata("Python Version", python_version)
      self.run.log_metadata("XGBoost Version", xgboost.__version__)
    self.run.log_model("XGBoost")
    self.run.log_metadata("Dataset columns", self.dtrain.num_col())
    self.run.log_metadata("Dataset rows", self.dtrain.num_row())
    for name in PARAMS_LOGGED_AS_METADATA:
      if name in self.params:
        self.run.log_metadata(name, self.params[name])
    if self.validation_sets is not None:
      self.run.log_metadata("Number of Test Sets", len(self.validation_sets))
      for pair in self.validation_sets:
        self.run.log_dataset(pair[1])

  def log_params(self):
    for name in self.params.keys():
      if name not in PARAMS_LOGGED_AS_METADATA:
        self.run.params.update({name: self.params[name]})

    self.run.params.num_boost_round = self.num_boost_round
    self.log_default_params()

  def log_default_params(self):
    params = get_all_run_params(self.model, num_boost_round=self.num_boost_round, **self.params)
    source = XGBOOST_DEFAULTS_SOURCE
    reported = self.run.params.keys()
    params = {k:v if v is not None else 'None' for k, v in params.items()
              if k not in reported and k not in PARAMS_LOGGED_AS_METADATA}
    self.run.set_parameters(params)
    self.run.set_parameters_sources_meta(source, sort=40, default_show=False)
    self.run.set_parameters_source(params, source)


  def check_learning_task(self):
    config = self.model.save_config()
    config_dict = json.loads(config)
    objective = config_dict['learner']['objective']['name']
    # NOTE: do not log metrics if learning task isn't regression or classification
    if not any(s in config_dict['learner']['objective']['name'] for s in SUPPORTED_OBJECTIVE_PREFIXES):
      self.run_options_parsed['log_metrics'] = False
    if objective.split(':')[0] == 'reg':
      self.is_regression = True
    else:
      self.is_regression = False

  def log_feature_importances(self, importance_type='weight', fmap=''):
    scores = self.model.get_score(importance_type=importance_type, fmap=fmap)
    # NOTE: do not log importances if there is no split at all.
    if not scores:
      return
    scores = dict(
      sorted(scores.items(), key=lambda x:(x[1], x[0]), reverse=True)[:FEATURE_IMPORTANCES_MAX_NUM_FEATURE]
    )
    fp = {
      'type': importance_type,
      'scores': scores,
    }
    self.run.log_sys_metadata('feature_importances', fp)

  def train_xgb(self):
    stream_monitor = SystemOutputStreamMonitor()
    with stream_monitor:
      xgb_args = {
        'params': self.params,
        'dtrain': self.dtrain,
        'num_boost_round': self.num_boost_round,
        'obj': self.obj,
        'feval': self.feval,
        'maximize': self.maximize,
        'early_stopping_rounds': self.early_stopping_rounds,
        'verbose_eval': self.verbose_eval,
        'xgb_model': self.model,
        'callbacks': self.callbacks,
      }
      if self.validation_sets is not None:
        self.evals_result = {} if self.evals_result is None else self.evals_result
        xgb_args['evals'] = self.validation_sets
        xgb_args['evals_result'] = self.evals_result
      t_start = time.time()
      bst = xgboost.train(**xgb_args)
      t_train = time.time() - t_start
      if self.run_options_parsed['log_metrics']:
        self.run.log_metric("Training time", t_train)
    stream_data = stream_monitor.get_stream_data()
    if stream_data:
      stdout, stderr = stream_data
      log_dict = {}
      if self.run_options_parsed['log_stdout']:
        log_dict["stdout"] = stdout
      if self.run_options_parsed['log_stderr']:
        log_dict["stderr"] = stderr
      self.run.set_logs(log_dict)
    self.model = bst

  def log_training_metrics(self):
    if self.run_options_parsed['log_metrics']:
      if self.is_regression:
        self.run.log_metrics(
          compute_regression_metrics(self.model, (self.dtrain, DEFAULT_TRAINING_NAME))
        )
      else:
        self.run.log_metrics(
          compute_classification_metrics(self.model, (self.dtrain, DEFAULT_TRAINING_NAME))
        )

  def log_validation_metrics(self):
    # Always log xgb-default eval_metric
    if self.evals_result is not None:
      for dataset, metric_dict in self.evals_result.items():
        for metric_label, metric_record in metric_dict.items():
          self.run.log_metric(f"{dataset}-{metric_label}", metric_record[-1])

    if self.run_options_parsed['log_metrics']:
      if self.validation_sets:
        for validation_set in self.validation_sets:
          if self.is_regression:
            self.run.log_metrics(
              compute_regression_metrics(self.model, (validation_set))
            )
          else:
            self.run.log_metrics(
              compute_classification_metrics(self.model, (validation_set))
            )


def run(
  params,
  dtrain,
  num_boost_round=10,
  obj=None,
  feval=None,
  maximize=None,
  evals=None,
  early_stopping_rounds=None,
  evals_result=None,
  verbose_eval=True,
  callbacks=None,
  xgb_model=None,
  run_options=None,
):
  """
  Sigopt integration for XGBoost mirrors the standard XGBoost train interface for the most part, with the option
  for additional arguments. Unlike the usual train interface, run() returns a context object, where context.run
  and context.model are the resulting RunContext and XGBoost model, respectively.
  """
  if evals is not None:
    if not isinstance(evals, (DMatrix, list)):
      dmatrix_module_name = '.'.join((DMatrix.__module__, DMatrix.__name__))
      raise TypeError(
        f"`evals` must be a {dmatrix_module_name} object or list of ({dmatrix_module_name}, str) tuples."
      )

  _run = XGBRun(
    params=params,
    dtrain=dtrain,
    num_boost_round=num_boost_round,
    obj=obj,
    feval=feval,
    maximize=maximize,
    evals=evals,
    early_stopping_rounds=early_stopping_rounds,
    evals_result=evals_result,
    verbose_eval=verbose_eval,
    xgb_model=xgb_model,
    callbacks=callbacks,
    run_options=run_options,
  )

  _run.make_run()
  _run.form_callbacks()
  _run.train_xgb()
  _run.log_metadata()
  if _run.run_options_parsed['log_params']:
    _run.log_params()
  _run.check_learning_task()
  _run.log_training_metrics()
  _run.log_validation_metrics()
  if _run.run_options_parsed['log_feature_importances']:
    _run.log_feature_importances()
  return Context(_run.run, _run.model)
