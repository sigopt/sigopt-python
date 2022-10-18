# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from ..arguments import experiment_file_option
from .run_base import run_command


def optimize_command(f):

  f = run_command(f)
  f = experiment_file_option(f)

  return f
