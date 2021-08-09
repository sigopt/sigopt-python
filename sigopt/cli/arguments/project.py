import click

from sigopt.defaults import check_valid_project_id


def validate_project_id_callback(ctx, p, value):
  try:
    check_valid_project_id(value)
  except ValueError as ve:
    raise click.BadParameter(str(ve)) from ve
  return value


project_option = click.option("--project", validate_project_id_callback)
