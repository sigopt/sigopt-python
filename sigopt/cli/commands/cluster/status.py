# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from ...arguments import identifiers_argument, identifiers_help
from .base import cluster_command


@cluster_command.command(
  context_settings=dict(ignore_unknown_options=True),
  help=f'''Get the status of the connected Kubernetes cluster. {identifiers_help}''',
)
@click.pass_context
@identifiers_argument
def status(ctx, identifiers):
  if identifiers:
    for i, identifier in enumerate(identifiers):
      if i > 0:
        print()
      ctx.obj.controller.print_status(identifier)
  else:
    ctx.obj.controller.cluster_status()
