# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from sigopt.config import config
from sigopt.factory import SigOptFactory

from ...utils import run_user_program
from ...arguments import project_option, source_file_option
from ..base import sigopt_cli
from ..run_base import run_command


@sigopt_cli.command(context_settings=dict(
  allow_interspersed_args=False,
  ignore_unknown_options=True,
))
@run_command
@source_file_option
@project_option
def run(command, run_options, source_file, project):
  '''Create a SigOpt Run.'''
  factory = SigOptFactory(project)
  factory.set_up_cli()
  with factory.create_run(name=run_options.get("name")) as run_context:
    run_user_program(config, run_context, command, source_file)
