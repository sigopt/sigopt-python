from sigopt.config import config

from ...utils import create_experiment_from_validated_data, cli_experiment_loop
from ..base import sigopt_cli
from ..optimize_base import optimize_command


@sigopt_cli.command(context_settings=dict(
  allow_interspersed_args=False,
  ignore_unknown_options=True,
))
@optimize_command
def optimize(command, run_options, experiment_file):
  '''Run a SigOpt Experiment.'''
  experiment = create_experiment_from_validated_data(experiment_file)
  cli_experiment_loop(config, experiment, command, run_options)
