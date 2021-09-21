from sigopt.config import config

from ...arguments import project_option, source_file_option
from ...utils import create_experiment_from_validated_data, cli_experiment_loop
from ..base import sigopt_cli
from ..optimize_base import optimize_command


@sigopt_cli.command(context_settings=dict(
  allow_interspersed_args=False,
  ignore_unknown_options=True,
))
@optimize_command
@source_file_option
@project_option
def optimize(command, run_options, experiment_file, source_file, project):
  '''Run a SigOpt Experiment.'''
  experiment = create_experiment_from_validated_data(experiment_file, project)
  cli_experiment_loop(config, experiment, command, run_options, source_file)
