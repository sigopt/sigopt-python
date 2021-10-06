import click
from sigopt.factory import SigOptFactory
from ...arguments import project_option
from ..base import archive_command


@archive_command.command("run")
@project_option
@click.argument("RUN_IDS", nargs=-1)
def archive(project, run_ids):
  '''Archive SigOpt Runs.'''
  factory = SigOptFactory(project)
  for run_id in run_ids:
    try:
      factory.archive_run(run_id)
    except Exception as e:
      raise click.ClickException(f'run_id: {run_id}, {e}') from e
