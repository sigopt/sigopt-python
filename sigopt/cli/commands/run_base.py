# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import functools

import click

from ..arguments import commands_argument, run_file_option


def run_command(f):

  @commands_argument
  @run_file_option
  @functools.wraps(f)
  def wrapper(*args, commands, run_file, **kwargs):
    if run_file:
      run_options = run_file.data
    else:
      run_options = {}
    if not commands:
      try:
        commands = run_options["run"]
      except KeyError as ke:
        raise click.UsageError(
          "Missing command: Please specify your run command via arguments or in the 'run' section of the run file."
        ) from ke
    return f(*args, command=commands, run_options=run_options, **kwargs)

  return wrapper
