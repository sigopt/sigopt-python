import click

from sigopt.defaults import check_valid_project_id, get_default_project


def validate_project_id_callback(ctx, p, value):
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
  help="Configure the project to use",
)
