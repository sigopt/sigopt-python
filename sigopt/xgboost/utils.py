# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import json

from .compat import Booster


def get_booster_params(booster):
  # refer:
  # https://github.com/dmlc/xgboost/blob/release_1.5.0/python-package/xgboost/sklearn.py#L522

  def parse_json_parameter_value(value):
    for convert_type in (int, float, str):
      try:
        ret = convert_type(value)
        return ret
      except ValueError:
        continue
    return str(value)

  assert isinstance(booster, Booster)
  config = json.loads(booster.save_config())
  stack = [config]
  all_xgboost_params = {}
  while stack:
    obj = stack.pop()
    for k, v in obj.items():
      if k.endswith('_param'):
        for p_k, p_v in v.items():
          all_xgboost_params[p_k] = p_v
      elif isinstance(v, dict):
        stack.append(v)

  params = {}
  for k, v in all_xgboost_params.items():
    params[k] = parse_json_parameter_value(v)

  return params
