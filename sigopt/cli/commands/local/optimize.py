from sigopt.config import config

<<<<<<< HEAD
from ...utils import run_user_program
from ...arguments import source_file_option
||||||| 7c15458
from ...utils import run_user_program
=======
from ...utils import create_experiment_from_validated_data, cli_experiment_loop
>>>>>>> sj/main
from ..base import sigopt_cli
from ..optimize_base import optimize_command


@sigopt_cli.command(context_settings=dict(
  allow_interspersed_args=False,
  ignore_unknown_options=True,
))
@optimize_command
@source_file_option
def optimize(command, run_options, experiment_file, source_file):
  '''Run a SigOpt Experiment.'''
  experiment = create_experiment_from_validated_data(experiment_file)
  cli_experiment_loop(config, experiment, command, run_options, source_file)
