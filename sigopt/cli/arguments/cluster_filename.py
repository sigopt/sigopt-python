# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from sigopt.validate import validate_top_level_dict

from .load_yaml import load_yaml_callback


cluster_filename_option = click.option(
  "-f",
  "--filename",
  type=click.Path(exists=True),
  callback=load_yaml_callback(validate_top_level_dict),
  help="cluster config yaml file",
  default="cluster.yml",
)
