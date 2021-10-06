import click
import sys
from sigopt.logging import print_logger
from sigopt.factory import SigOptFactory
from ...arguments import project_option
from .base import experiment_command


@experiment_command.command()
@click.argument("EXPERIMENT_ID")
@project_option
def unarchive(experiment_id, project):
  '''unarchive a SigOpt Experiment.'''
  try:
    factory = SigOptFactory(project)
    factory.connection.experiments(experiment_id).update(state="active")
  except Exception as e:
    print_logger.error(f'Error: {e}')
    sys.exit(-1)
