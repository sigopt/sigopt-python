# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from sigopt.validate import validate_top_level_dict

from ...arguments import load_yaml_callback
from .base import cluster_command


@cluster_command.command()
@click.option(
  '-f',
  '--filename',
  type=click.Path(exists=True),
  callback=load_yaml_callback(validate_top_level_dict),
  help='cluster config yaml file',
  default='cluster.yml',
)
@click.pass_context
def create(ctx, filename):
  '''Create a Kubernetes cluster.'''
  ctx.obj.controller.create_cluster(filename.data)
