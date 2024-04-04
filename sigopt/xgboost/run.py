# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import copy
import json
import math
import platform
import time
import warnings
from inspect import signature

from .. import create_run
from ..log_capture import SystemOutputStreamMonitor
from ..model_aware_run import ModelAwareRun
from ..run_context import RunContext
from .checkpoint_callback import SigOptCheckpointCallback
from .compat import Booster, DMatrix, xgboost
from .compute_metrics import compute_classification_metrics, compute_regression_metrics
from .constants import (
  DEFAULT_EVALS_NAME,
  USER_SOURCE_NAME,
  USER_SOURCE_PRIORITY,
  XGBOOST_DEFAULTS_SOURCE_NAME,
  XGBOOST_DEFAULTS_SOURCE_PRIORITY,
)
from .utils import get_booster_params


DEFAULT_RUN_OPTIONS = {
  "autolog_checkpoints": True,
  "autolog_feature_importances": True,
  "autolog_metrics": True,
  "autolog_stdout": True,
  "autolog_stderr": True,
  "autolog_sys_info": True,
  "autolog_xgboost_defaults": True,
  "name": None,
  "run": None,
}
DEFAULT_CHECKPOINT_PERIOD = 5
MAX_NUM_CHECKPOINTS = 200
FEATURE_IMPORTANCES_MAX_NUM_FEATURE = 50
FEATURE_IMPORTANCES_MAX_KEY_CHARS = 100
XGB_INTEGRATION_KEYWORD = "_IS_XGB_RUN"

PARAMS_LOGGED_AS_METADATA = [
  "eval_metric",
  "interaction_constraints",
  "monotone_constraints",
  "num_class",
  "objective",
  "updater",
]
SUPPORTED_OBJECTIVE_PREFIXES = [
  "binary",
  "multi",
  "reg",
]
DOC_URL = "https://docs.sigopt.com/ai-module-api-references/xgboost/xgboost_run"


def parse_run_options(run_options):
  if run_options is None:
    return copy.deepcopy(DEFAULT_RUN_OPTIONS)

  if not isinstance(run_options, dict):
    raise TypeError(f"run_options should be a dictionary. Refer to the sigopt.xgboost.run documentation {DOC_URL}")

  if run_options.keys() - DEFAULT_RUN_OPTIONS.keys():
    raise ValueError(f"Unsupported keys {run_options.keys() - DEFAULT_RUN_OPTIONS.keys()} in run_options.")

  for key, value in run_options.items():
    if key.startswith("autolog") and not isinstance(value, bool):
      raise TypeError(f"run_options key `{key}` expects a Boolean value, not {type(value)}.")

  if {"run", "name"}.issubset(run_options.keys()):
    if run_options["run"] and run_options["name"]:
      raise ValueError("Cannot specify both `run` and `name` keys inside run_options.")

  if "run" in run_options.keys() and run_options["run"] is not None:
    if not isinstance(run_options["run"], RunContext):
      raise TypeError(f"`run` must be an instance of RunContext object, not {type(run_options['run']).__name__}.")

  return {**DEFAULT_RUN_OPTIONS, **run_options}


def validate_xgboost_kwargs(xgb_kwargs):
  if not xgb_kwargs:
    return

  for key in list(xgb_kwargs.keys()):
    if key not in signature(xgboost.train).parameters.keys():
      warnings.warn(
        f"The argument `{key}` is not supported by this version of XGBoost, and has been ignored",
        RuntimeWarning,
      )
      xgb_kwargs.pop(key)


class XGBRun(ModelAwareRun):
  def __init__(self, run, model):
    assert isinstance(model, Booster)
    super().__init__(run, model)


class XGBRunHandler:
  def __init__(
    self,
    params,
    dtrain,
    num_boost_round,
    evals,
    early_stopping_rounds,
    evals_result,
    verbose_eval,
    xgb_model,
    callbacks,
    run_options,
    **kwargs,
  ):
    self.params = params
    self.dtrain = dtrain
    self.num_boost_round = num_boost_round
    self.early_stopping_rounds = early_stopping_rounds
    self.verbose_eval = verbose_eval
    self.callbacks = callbacks
    self.validation_sets = [(evals, DEFAULT_EVALS_NAME)] if isinstance(evals, DMatrix) else evals
    self.evals_result = evals_result
    self.run_options_parsed = parse_run_options(run_options)
    self.run = None
    self.model = xgb_model
    self.is_regression = None
    self.kwargs = kwargs
    validate_xgboost_kwargs(self.kwargs)

  def form_callbacks(self):
    # if no validation set, checkpointing not possible
    if not (self.run_options_parsed["autolog_checkpoints"] and self.validation_sets):
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
    if self.run_options_parsed["run"] is not None:
      self.run = self.run_options_parsed["run"]
    elif self.run_options_parsed["name"] is not None:
      self.run = create_run(name=self.run_options_parsed["name"])
    else:
      self.run = create_run()

  def log_metadata(self):
    self.run.log_dev_metadata(XGB_INTEGRATION_KEYWORD, True)

    if self.run_options_parsed["autolog_sys_info"]:
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

  def _log_param_by_source(self, param_name, value, source_name):
    self.run.params.update({param_name: value})
    self.run.set_parameter_source(param_name, source_name)

  def log_params(self):
    self.run.set_parameters_sources_meta(USER_SOURCE_NAME, sort=USER_SOURCE_PRIORITY, default_show=True)
    for p_name, p_value in self.params.items():
      if p_name not in self.run.params and p_name not in PARAMS_LOGGED_AS_METADATA:
        self._log_param_by_source(p_name, p_value, USER_SOURCE_NAME)

    if "num_boost_round" not in self.run.params.keys():
      self._log_param_by_source("num_boost_round", self.num_boost_round, USER_SOURCE_NAME)

    if self.early_stopping_rounds is not None and "early_stopping_rounds" not in self.run.params.keys():
      self._log_param_by_source("early_stopping_rounds", self.early_stopping_rounds, USER_SOURCE_NAME)

    if self.run_options_parsed["autolog_xgboost_defaults"]:
      self.log_default_params()

  def log_default_params(self):
    all_xgb_params = get_booster_params(self.model)
    reported_params = self.run.params.keys()

    xgb_default_params = {}
    self.run.set_parameters_sources_meta(
      XGBOOST_DEFAULTS_SOURCE_NAME,
      sort=XGBOOST_DEFAULTS_SOURCE_PRIORITY,
      default_show=False,
    )
    for p_name, p_value in all_xgb_params.items():
      if p_name not in reported_params and p_name not in PARAMS_LOGGED_AS_METADATA:
        if p_value is not None:
          xgb_default_params.update({p_name: p_value})
    self.run.set_parameters(xgb_default_params)
    self.run.set_parameters_source(xgb_default_params, XGBOOST_DEFAULTS_SOURCE_NAME)

  def check_learning_task(self):
    config = self.model.save_config()
    config_dict = json.loads(config)
    objective = config_dict["learner"]["objective"]["name"]
    # NOTE: do not log metrics if learning task isn't regression or classification
    if not any(s in config_dict["learner"]["objective"]["name"] for s in SUPPORTED_OBJECTIVE_PREFIXES):
      self.run_options_parsed["autolog_metrics"] = False
    if objective.split(":")[0] == "reg":
      self.is_regression = True
    else:
      self.is_regression = False

  def log_feature_importances(self, importance_type="weight", fmap=""):
    scores = self.model.get_score(importance_type=importance_type, fmap=fmap)
    # NOTE: do not log importances if there is no split at all.
    if not scores:
      return
    scores = dict(
      sorted(scores.items(), key=lambda x: (x[1], x[0]), reverse=True)[:FEATURE_IMPORTANCES_MAX_NUM_FEATURE]
    )

    if any(len(k) > FEATURE_IMPORTANCES_MAX_KEY_CHARS for k in scores.keys()):
      warnings.warn(
        (
          "Some of the feature names have more than"
          f" {FEATURE_IMPORTANCES_MAX_KEY_CHARS} characters, skipping logging"
          " feature importances."
        ),
        RuntimeWarning,
      )
      return

    fp = {
      "type": importance_type,
      "scores": scores,
    }
    self.run.log_sys_metadata("feature_importances", fp)

  def train_xgb(self):
    stream_monitor = SystemOutputStreamMonitor()
    with stream_monitor:
      params = copy.deepcopy(self.params)
      if self.run.params:
        params.update(self.run.params)
        if "num_boost_round" in params:
          self.num_boost_round = params.pop("num_boost_round")
        if "early_stopping_rounds" in params:
          self.early_stopping_rounds = params.pop("early_stopping_rounds")
      xgb_args = {
        "params": params,
        "dtrain": self.dtrain,
        "num_boost_round": self.num_boost_round,
        "early_stopping_rounds": self.early_stopping_rounds,
        "verbose_eval": self.verbose_eval,
        "xgb_model": self.model,
        "callbacks": self.callbacks,
      }
      if self.kwargs:
        xgb_args.update(self.kwargs)
      if self.validation_sets is not None:
        self.evals_result = {} if self.evals_result is None else self.evals_result
        xgb_args["evals"] = self.validation_sets
        xgb_args["evals_result"] = self.evals_result
      t_start = time.time()
      bst = xgboost.train(**xgb_args)
      t_train = time.time() - t_start
      if self.run_options_parsed["autolog_metrics"]:
        self.run.log_metric("Training time", t_train)

    stream_data = stream_monitor.get_stream_data()
    if stream_data:
      stdout, stderr = stream_data
      log_dict = {}
      if self.run_options_parsed["autolog_stdout"]:
        log_dict["stdout"] = stdout
      if self.run_options_parsed["autolog_stderr"]:
        log_dict["stderr"] = stderr
      self.run.set_logs(log_dict)
    self.model = bst

  def log_validation_metrics(self):
    # Always log xgb-default eval_metric
    n_eval_rounds = 0
    if self.evals_result is not None:
      for dataset, metric_dict in self.evals_result.items():
        for metric_label, metric_record in metric_dict.items():
          self.run.log_metric(f"{dataset}-{metric_label}", metric_record[-1])
          n_eval_rounds = len(metric_record)

      if self.early_stopping_rounds:
        self.run.log_metric("num_boost_round_before_stopping", n_eval_rounds)

    if self.run_options_parsed["autolog_metrics"] and self.validation_sets:
      for validation_set in self.validation_sets:
        if self.is_regression:
          self.run.log_metrics(compute_regression_metrics(self.model, (validation_set)))
        else:
          self.run.log_metrics(compute_classification_metrics(self.model, (validation_set)))


def run(
  params,
  dtrain,
  num_boost_round=10,
  evals=None,
  early_stopping_rounds=None,
  evals_result=None,
  verbose_eval=True,
  callbacks=None,
  xgb_model=None,
  run_options=None,
  **kwargs,
):
  """
    Sigopt integration for XGBoost mirrors the standard xgboost.train interface for the most part, with the option
    for additional arguments. Unlike the usual train interface, sigopt.xgboost.run() returns a XGBRun object,
    where XGBRun.run and XGBRun.model are the resulting RunContext and XGBoost model, respectively.
    """
  if evals is not None:
    if not isinstance(evals, (DMatrix, list)):
      dmatrix_module_name = ".".join((DMatrix.__module__, DMatrix.__name__))
      raise TypeError(f"`evals` must be a {dmatrix_module_name} object or list of ({dmatrix_module_name}, str) tuples.")

  _run = XGBRunHandler(
    params=params,
    dtrain=dtrain,
    num_boost_round=num_boost_round,
    evals=evals,
    early_stopping_rounds=early_stopping_rounds,
    evals_result=evals_result,
    verbose_eval=verbose_eval,
    xgb_model=xgb_model,
    callbacks=callbacks,
    run_options=run_options,
    **kwargs,
  )

  _run.make_run()
  _run.form_callbacks()
  _run.train_xgb()
  _run.log_metadata()
  _run.log_params()
  _run.check_learning_task()
  _run.log_validation_metrics()
  if _run.run_options_parsed["autolog_feature_importances"]:
    _run.log_feature_importances()
  return XGBRun(_run.run, _run.model)
