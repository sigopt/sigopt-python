from sigopt.config import config

from ...utils import create_experiment_from_validated_data, run_user_program
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
  for run_context in experiment.loop(name=run_options.get("name")):
    with run_context:
      run_user_program(config, run_context, command)
