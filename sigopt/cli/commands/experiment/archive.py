# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click
from sigopt.factory import SigOptFactory
from ...arguments import project_option, validate_ids
from ..base import archive_command


@archive_command.command("experiment")
@project_option
@click.argument("EXPERIMENT_IDS", nargs=-1, callback=validate_ids)
def archive(project, experiment_ids):
  '''Archive SigOpt Experiments.'''
  factory = SigOptFactory(project)
  factory.set_up_cli()
  for experiment_id in experiment_ids:
    try:
      factory.connection.experiments(experiment_id).delete()
    except Exception as e:
      raise click.ClickException(f"experiment_id: {experiment_id}, {e}") from e
