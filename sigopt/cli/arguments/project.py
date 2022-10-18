# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from sigopt.defaults import check_valid_project_id, get_default_project


def validate_project_id_callback(ctx, p, value):  # pylint: disable=unused-argument
  if value is None:
    return get_default_project()
  try:
    check_valid_project_id(value)
  except ValueError as ve:
    raise click.BadParameter(str(ve)) from ve
  return value


project_option = click.option(
  "-p",
  "--project",
  callback=validate_project_id_callback,
  help="""
  Provide the project ID.
  Projects can be created at https://app.sigopt.com/projects or with the command `sigopt create project`.
  If a project ID is not provided then the project ID is determined in the following order:
  first from the SIGOPT_PROJECT environment variable, then by the name of the current directory.
  """,
)

def validate_project_name_callback(ctx, p, value):  # pylint: disable=unused-argument
  if value is None:
    return get_default_project()
  return value

project_name_option = click.option(
  '--project-name',
  callback=validate_project_name_callback,
  help="The name of the project.",
)
