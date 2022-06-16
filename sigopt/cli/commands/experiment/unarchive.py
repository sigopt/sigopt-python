import click
from sigopt.factory import SigOptFactory
from ...arguments import project_option, validate_ids
from ..base import unarchive_command


@unarchive_command.command("experiment")
@project_option
@click.argument("EXPERIMENT_IDS", nargs=-1, callback=validate_ids)
def unarchive(project, experiment_ids):
  '''Unarchive SigOpt Experiments.'''
  factory = SigOptFactory(project)
  factory.set_up_cli()
  for experiment_id in experiment_ids:
    try:
      factory.unarchive_experiment(experiment_id)
    except Exception as e:
      raise click.ClickException(f'experiment_id: {experiment_id}, {e}') from e
