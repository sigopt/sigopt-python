# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from sigopt.validate import validate_run_input

from .load_yaml import load_yaml_callback


run_file_option = click.option(
  '-r',
  '--run-file',
  default='run.yml',
  type=click.Path(),
  callback=load_yaml_callback(validate_run_input, ignore_no_file=True),
  help="A YAML file that defines your run. The contents will be stored as data on your run.",
)
