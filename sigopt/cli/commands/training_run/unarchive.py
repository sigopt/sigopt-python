# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click
from sigopt.factory import SigOptFactory
from ...arguments import project_option, validate_ids
from ..base import unarchive_command

@unarchive_command.command("run")
@project_option
@click.argument("RUN_IDS", nargs=-1, callback=validate_ids)
def unarchive(project, run_ids):
  '''Unarchive SigOpt Runs.'''
  factory = SigOptFactory(project)
  factory.set_up_cli()
  for run_id in run_ids:
    try:
      factory.unarchive_run(run_id)
    except Exception as e:
      raise click.ClickException(f'run_id: {run_id}, {e}') from e
