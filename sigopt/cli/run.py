import click

from ..config import config
from ..defaults import get_default_project
from ..factory import SigOptFactory
from .cli import cli
from .utils import check_path, run_user_program, setup_cli


@cli.command(context_settings=dict(
  ignore_unknown_options=True,
))
@click.argument('entrypoint')
@click.argument('entrypoint_args', nargs=-1, type=click.UNPROCESSED)
def run(entrypoint, entrypoint_args):
  check_path(
    entrypoint,
    "Provided entrypoint '{entrypoint}' does not exist",
  )
  setup_cli(config)
  project_id = get_default_project()
  factory = SigOptFactory(project_id)
  with factory.create_run() as run_context:
    run_user_program(config, run_context, entrypoint, entrypoint_args)
