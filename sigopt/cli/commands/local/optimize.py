from sigopt.config import config
from sigopt.defaults import get_default_project
from sigopt.factory import SigOptFactory

from ...utils import run_user_program
from ...arguments import source_file_option
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
  experiment_input = experiment_file.data
  project_id = get_default_project()
  factory = SigOptFactory(project_id)
  experiment = factory.create_prevalidated_experiment(experiment_input)
  for run_context in experiment.loop(name=run_options.get("name")):
    with run_context:
      run_user_program(config, run_context, command, source_file)
