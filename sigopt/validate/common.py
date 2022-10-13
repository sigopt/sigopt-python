# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from .exceptions import ValidationError


def validate_top_level_dict(input_data):
  if input_data is None:
    return {}
  if not isinstance(input_data, dict):
    raise ValidationError('The top level should be a mapping of keys to values')
  return input_data
