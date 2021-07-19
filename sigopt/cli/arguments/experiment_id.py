import click


def validate_id(ctx, param, value):
  if value.isdigit():
    return value
  raise click.BadParameter("must be a string of digits")

experiment_id_argument = click.argument("EXPERIMENT_ID", callback=validate_id)
