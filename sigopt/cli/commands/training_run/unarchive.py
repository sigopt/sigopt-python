import click
import sys
from sigopt.logging import print_logger
from sigopt.factory import SigOptFactory
from ...arguments import project_option
from .base import training_run_command


@training_run_command.command()
@click.argument("RUN_ID")
@project_option
def unarchive(run_id, project):
  '''unarchive a SigOpt TrainingRun.'''
  try:
    factory = SigOptFactory(project)
    factory.connection.training_runs(run_id).update(deleted=False)
  except Exception as e:
    print_logger.error(f'Error: {e}')
    sys.exit(-1)
