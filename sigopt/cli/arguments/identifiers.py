# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from sigopt.orchestrate.identifier import parse_identifier


def identifiers_callback(ctx, p, value):  # pylint: disable=unused-argument
  try:
    return [parse_identifier(raw) for raw in value]
  except ValueError as ve:
    raise click.BadParameter(str(ve)) from ve


identifiers_argument = click.argument(
  "identifiers",
  nargs=-1,
  callback=identifiers_callback,
)

identifiers_help = "IDENTIFIERS can be the name of a run, or one of the following: experiment/[id], run/[id]"
