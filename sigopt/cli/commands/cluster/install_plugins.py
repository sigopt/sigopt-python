# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from .base import cluster_command


@cluster_command.command()
@click.pass_context
def install_plugins(ctx):
  """Install plugins on the connected Kubernetes cluster."""
  ctx.obj.controller.install_cluster_plugins()
