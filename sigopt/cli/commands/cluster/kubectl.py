# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from .base import cluster_command


@cluster_command.command(
  add_help_option=False,
  context_settings=dict(
    allow_interspersed_args=False,
    ignore_unknown_options=True,
  ),
)
@click.pass_context
@click.argument(
  "kubectl_arguments",
  nargs=-1,
  type=click.UNPROCESSED,
)
def kubectl(ctx, kubectl_arguments):
  '''Run kubectl with the connected Kubernetes cluster.'''
  ctx.obj.controller.exec_kubectl(kubectl_arguments)
