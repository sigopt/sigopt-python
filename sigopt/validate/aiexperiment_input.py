# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from sigopt.lib import is_integer, is_mapping, is_number, is_sequence, is_string, validate_name

from .common import validate_top_level_dict
from .exceptions import ValidationError
from .keys import PROJECT_KEY


def get_validated_name(aiexperiment_input):
  try:
    name = aiexperiment_input.pop("name")
  except KeyError as ke:
    raise ValidationError("name is required") from ke
  try:
    validate_name("AIExperiment name", name)
  except ValueError as ve:
    raise ValidationError(str(ve)) from ve
  return name


def get_validated_metric(metric_input):
  validated_metric = {}

  if is_mapping(metric_input):
    metric = dict(metric_input)
  else:
    raise ValidationError("all metrics must be a mapping of keys to values")

  try:
    metric_name = metric["name"]
  except KeyError as ke:
    raise ValidationError("all metrics require a name") from ke

  try:
    validate_name("metric name", metric_name)
  except ValueError as ve:
    raise ValidationError(str(ve)) from ve

  validated_metric["name"] = metric_name
  metric_strategy = metric.pop("strategy", None)
  if metric_strategy is not None:
    try:
      validate_name("metric strategy", metric_strategy)
    except ValueError as ve:
      raise ValidationError(str(ve)) from ve
    validated_metric["strategy"] = metric_strategy
  metric_objective = metric.pop("objective", None)
  if metric_objective is not None:
    try:
      validate_name("metric objective", metric_objective)
    except ValueError as ve:
      raise ValidationError(str(ve)) from ve
    validated_metric["objective"] = metric_objective
  metric_threshold = metric.pop("threshold", None)
  if metric_threshold is not None:
    if not is_number(metric_threshold):
      raise ValidationError("metric threshold must be a number")
    validated_metric["threshold"] = metric_threshold
  for key, value in metric.items():
    if key not in validated_metric:
      if not is_string(key):
        raise ValidationError("all metric keys must be strings")
      validated_metric[key] = value
  return validated_metric


def get_validated_metrics(aiexperiment_input):
  try:
    metrics = aiexperiment_input.pop("metrics")
  except KeyError as ke:
    raise ValidationError("a list of metrics is required") from ke
  if not is_sequence(metrics):
    raise ValidationError("metrics must be a non-empty list")
  metrics = list(metrics)
  if not metrics:
    raise ValidationError("metrics must be a non-empty list")
  validated_metrics = [get_validated_metric(metric) for metric in metrics]
  return validated_metrics


def get_validated_parameters(aiexperiment_input):
  try:
    parameters = aiexperiment_input.pop("parameters")
  except KeyError as ke:
    raise ValidationError("a list of parameters is required") from ke
  if not is_sequence(parameters):
    raise ValidationError("parameters must be a non-empty list")
  parameters = list(parameters)
  if not parameters:
    raise ValidationError("parameters must be a non-empty list")
  validated_parameters = []
  for param in parameters:
    validated_param = {}
    if not is_mapping(param):
      raise ValidationError("all parameters must be a mapping of keys to values")
    try:
      param_name = param["name"]
    except KeyError as ke:
      raise ValidationError("all parameters require a name") from ke
    try:
      validate_name("parameter name", param_name)
    except ValueError as ve:
      raise ValidationError(str(ve)) from ve
    validated_param["name"] = param_name
    try:
      param_type = param["type"]
    except KeyError as ke:
      raise ValidationError("all parameters require a type") from ke
    try:
      validate_name("parameter type", param_type)
    except ValueError as ve:
      raise ValidationError(str(ve)) from ve
    validated_param["type"] = param_type
    for key, value in param.items():
      if key not in validated_param:
        if not is_string(key):
          raise ValidationError("all parameter keys must be strings")
        validated_param[key] = value
    validated_parameters.append(validated_param)
  return validated_parameters


def get_validated_budget(aiexperiment_input):
  budget = aiexperiment_input["budget"]
  if not (budget is None or is_number(budget) and budget >= 0):
    raise ValidationError("budget must be a non-negative number")
  if budget == float("inf"):
    raise ValidationError("budget cannot be infinity")
  return budget


def get_validated_parallel_bandwidth(aiexperiment_input):
  parallel_bandwidth = aiexperiment_input.pop("parallel_bandwidth")
  if parallel_bandwidth is None or is_integer(parallel_bandwidth) and parallel_bandwidth > 0:
    return parallel_bandwidth
  raise ValidationError("parallel_bandwidth must be a positive integer")


def validate_aiexperiment_input(aiexperiment_input):
  aiexperiment_input = validate_top_level_dict(aiexperiment_input)
  if PROJECT_KEY in aiexperiment_input:
    raise ValidationError(
      "The project field is not permitted in the AIExperiment."
      " Please set the SIGOPT_PROJECT environment variable instead."
    )
  aiexperiment_input = dict(aiexperiment_input)
  validated = {}
  validated["name"] = get_validated_name(aiexperiment_input)
  validated["parameters"] = get_validated_parameters(aiexperiment_input)
  validated["metrics"] = get_validated_metrics(aiexperiment_input)
  try:
    validated["budget"] = get_validated_budget(aiexperiment_input)
  except KeyError:
    pass
  try:
    validated["parallel_bandwidth"] = get_validated_parallel_bandwidth(aiexperiment_input)
  except KeyError:
    pass
  for key, value in aiexperiment_input.items():
    if not is_string(key):
      raise ValidationError("all AIExperiment keys must be strings")
    validated[key] = value
  return validated


def validate_aiexperiment_update_input(aiexperiment_input):
  aiexperiment_input = validate_top_level_dict(aiexperiment_input)
  if PROJECT_KEY in aiexperiment_input:
    raise ValidationError(
      "The project field is not permitted in the AIExperiment."
      " Please set the SIGOPT_PROJECT environment variable instead."
    )
  aiexperiment_input = dict(aiexperiment_input)
  validated = {}
  try:
    validated["name"] = get_validated_name(aiexperiment_input)
  except KeyError:
    pass

  try:
    validated["parameters"] = get_validated_parameters(aiexperiment_input)
  except KeyError:
    pass

  if "metrics" in aiexperiment_input:
    validated["metrics"] = get_validated_metrics(aiexperiment_input)

  try:
    validated["budget"] = get_validated_budget(aiexperiment_input)
  except KeyError:
    pass

  try:
    validated["parallel_bandwidth"] = get_validated_parallel_bandwidth(aiexperiment_input)
  except KeyError:
    pass

  for key, value in aiexperiment_input.items():
    if not is_string(key):
      raise ValidationError("all AIExperiment keys must be strings")
    validated[key] = value
  return validated
