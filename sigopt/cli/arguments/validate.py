# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click


def validate_id(ctx, param, value):
  if value.isdigit():
    return value
  raise click.BadParameter("ID must be a string of digits")


def validate_ids(ctx, param, value):
  return [validate_id(ctx, param, item) for item in value]
