from sigopt.config import config
from sigopt.defaults import get_default_project
from sigopt.factory import SigOptFactory

from ...utils import run_user_program
from ..base import sigopt_cli
from ..run_base import run_command


@sigopt_cli.command(context_settings=dict(
  allow_interspersed_args=False,
  ignore_unknown_options=True,
))
@run_command
def run(command, run_options):
  '''Create a SigOpt Run.'''
  project_id = get_default_project()
  factory = SigOptFactory(project_id)
  with factory.create_run(name=run_options.get("name")) as run_context:
    run_user_program(config, run_context, command)
