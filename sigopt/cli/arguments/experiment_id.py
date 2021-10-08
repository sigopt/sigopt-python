import click

from .validate import validate_id
experiment_id_argument = click.argument("EXPERIMENT_ID", callback=validate_id)
