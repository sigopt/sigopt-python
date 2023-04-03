# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from .run_context import RunContext


class ModelAwareRun:
  def __init__(self, run, model):
    assert isinstance(run, RunContext)
    self.run = run
    self.model = model
