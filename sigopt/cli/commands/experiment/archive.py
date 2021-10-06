import click
import sys
from sigopt.logging import print_logger
from sigopt.factory import SigOptFactory
from ...arguments import project_option
from .base import experiment_command


@experiment_command.command()
@click.argument("EXPERIMENT_ID")
@project_option
def archive(experiment_id, project):
  '''archive a SigOpt Experiment.'''
  try:
    factory = SigOptFactory(project)
    factory.connection.experiments(experiment_id).delete()
  except Exception as e:
    print_logger.error(f'Error: {e}')
    sys.exit(-1)
