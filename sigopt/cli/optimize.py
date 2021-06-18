import click
import yaml

from ..config import config
from ..defaults import get_default_project
from ..experiment_context import create_experiment
from ..vendored import six
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
    six.u("Provided entrypoint '{entrypoint}' does not exist").format(entrypoint=entrypoint),
  )
  check_path(
    sigopt_file,
    six.u("The sigopt file '{sigopt_file}' is missing").format(sigopt_file=sigopt_file),
  )
  sigopt_input = load_yaml(sigopt_file)
  experiment_input = get_and_validate_experiment_input(sigopt_input, sigopt_file)
  setup_cli(config)
  project_id = get_default_project()
  experiment = create_experiment(project=project_id, **experiment_input)
  for run_context in experiment.loop():
    with run_context:
      run_user_program(config, run_context, entrypoint, entrypoint_args)
