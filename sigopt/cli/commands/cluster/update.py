# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from ...arguments import cluster_filename_option
from .base import cluster_command


@cluster_command.command()
@cluster_filename_option
@click.pass_context
def update(ctx, filename):
  '''Update the connected Kuberentes cluster.'''
  ctx.obj.controller.update_cluster(filename.data)
