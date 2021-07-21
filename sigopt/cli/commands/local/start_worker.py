from sigopt.config import config
from sigopt.factory import SigOptFactory

from ...utils import cli_experiment_loop
from ...arguments import experiment_id_argument, source_file_option
from ..base import sigopt_cli
from ..run_base import run_command


@sigopt_cli.command()
@experiment_id_argument
@run_command
@source_file_option
def start_worker(experiment_id, command, run_options, source_file):
  '''Start a worker for the given Experiment.'''
  factory = SigOptFactory.from_default_project()
  experiment = factory.get_experiment(experiment_id)
  cli_experiment_loop(config, experiment, command, run_options, source_file)
