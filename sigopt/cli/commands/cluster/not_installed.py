# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from ..base import sigopt_cli


INSTALLATION_MESSAGE = " ".join([
  "Orchestrate is not installed.",
  "Please run the following to enable the cluster subcommand:",
  "`pip install 'sigopt[orchestrate]'",
])

@sigopt_cli.command(help=INSTALLATION_MESSAGE)
@click.argument(
  "_",
  nargs=-1,
  type=click.UNPROCESSED,
)
def cluster(_):
  print(INSTALLATION_MESSAGE)
