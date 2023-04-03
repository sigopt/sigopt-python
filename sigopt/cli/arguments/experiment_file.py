# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from sigopt.validate import validate_aiexperiment_input

from .load_yaml import load_yaml_callback


experiment_file_option = click.option(
  "-e",
  "--experiment-file",
  default="experiment.yml",
  type=click.Path(exists=True),
  callback=load_yaml_callback(validate_aiexperiment_input),
  help="A YAML file that defines your AIExperiment.",
)
