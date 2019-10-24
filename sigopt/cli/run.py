import click

from ..runs.factory import RunFactory
from ..vendored import six
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
    six.u("Provided entrypoint '{entrypoint}' does not exist").format(entrypoint=entrypoint),
  )
  setup_cli()
  run_user_program(RunFactory(), entrypoint, entrypoint_args)
