import click
import yaml

from ..config import config
from ..defaults import get_default_project
from ..factory import SigOptFactory
from .cli import cli
from .validate import EXPERIMENT_KEY, validate_experiment_input, validate_sigopt_input
from .utils import check_path, run_user_program, setup_cli


def load_yaml(yaml_path):
  with open(yaml_path) as yaml_fp:
    return yaml.safe_load(yaml_fp)

def get_and_validate_experiment_input(sigopt_input, filename):
  sigopt_input = validate_sigopt_input(sigopt_input, filename)
  experiment_input = validate_experiment_input(sigopt_input.get(EXPERIMENT_KEY), filename)
  return experiment_input

@cli.command(context_settings=dict(
  ignore_unknown_options=True,
))
@click.argument('entrypoint')
@click.argument('entrypoint_args', nargs=-1, type=click.UNPROCESSED)
@click.option('--sigopt-file', default='sigopt.yml')
def optimize(entrypoint, entrypoint_args, sigopt_file):
  check_path(
    entrypoint,
    f"Provided entrypoint '{entrypoint}' does not exist",
  )
  check_path(
    sigopt_file,
    f"The sigopt file '{sigopt_file}' is missing",
  )
  sigopt_input = load_yaml(sigopt_file)
  experiment_input = get_and_validate_experiment_input(sigopt_input, sigopt_file)
  setup_cli(config)
  project_id = get_default_project()
  factory = SigOptFactory(project_id)
  experiment = factory.create_experiment(**experiment_input)
  for run_context in experiment.loop():
    with run_context:
      run_user_program(config, run_context, entrypoint, entrypoint_args)
