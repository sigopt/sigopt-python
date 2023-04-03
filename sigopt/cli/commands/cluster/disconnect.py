# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from .base import cluster_command


@cluster_command.command()
@click.pass_context
def disconnect(ctx):
  """Disconnect from the connected Kubernetes cluster."""
  ctx.obj.controller.disconnect_from_connected_cluster()
