import click
from sigopt.factory import SigOptFactory
from ...arguments import project_option
from .base import experiment_command


@experiment_command.command()
@click.argument("EXPERIMENT_ID")
@project_option
def archive(experiment_id, project):
  '''Archive a SigOpt Experiment.'''
  try:
    factory = SigOptFactory(project)
    factory.connection.experiments(experiment_id).delete()
  except Exception as e:
    raise click.ClickException(f'experiment_id: {experiment_id}, {e}') from e
