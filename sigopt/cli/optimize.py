import click
import yaml

from ..optimization import optimization_loop
from ..defaults import ensure_project_exists, get_default_project
from ..run_factory import RunFactory
from ..vendored import six
from .cli import cli
from .validate import EXPERIMENT_KEY, PROJECT_KEY, validate_experiment_input, validate_sigopt_input
from .utils import check_path, run_user_program, setup_cli


def load_yaml(yaml_path):
  with open(yaml_path) as yaml_fp:
    return yaml.safe_load(yaml_fp)

def get_and_validate_experiment_input(sigopt_input, filename):
  sigopt_input = validate_sigopt_input(sigopt_input, filename)
  experiment_input = validate_experiment_input(sigopt_input.get(EXPERIMENT_KEY), filename)
  return experiment_input

def create_experiment_from_input(connection, experiment_input):
  return connection.experiments().create(**experiment_input)

def run_experiment(run_factory, entrypoint, entrypoint_args, connection, experiment_input):
  project_id = get_default_project()
  ensure_project_exists(connection, project_id)
  experiment_input[PROJECT_KEY] = project_id
  experiment = create_experiment_from_input(connection, experiment_input)

  def loop_body(suggestion):
    run_user_program(run_factory, entrypoint, entrypoint_args, suggestion=suggestion)

  optimization_loop(connection, experiment, loop_body)

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
  setup_cli()
  run_factory = RunFactory()
  connection = run_factory.connection
  run_experiment(run_factory, entrypoint, entrypoint_args, connection, experiment_input)
