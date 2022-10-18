# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from ...arguments import identifiers_argument, identifiers_help
from .base import cluster_command


@cluster_command.command(help=f'''Stop a Run or Experiment. {identifiers_help}''')
@click.pass_context
@identifiers_argument
def stop(ctx, identifiers):
  if not identifiers:
    print("No identifiers provided, nothing to do.")
    return
  for identifier in identifiers:
    ctx.obj.controller.stop_by_identifier(identifier)
