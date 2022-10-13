# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from .defaults import get_default_name
from .sigopt_logging import print_logger
from .run_context import RunContext


class BaseRunFactory(object):
  run_context_class = RunContext

  def _on_run_created(self, run):
    print_logger.info("Run started, view it on the SigOpt dashboard at https://app.sigopt.com/run/%s", run.id)

  @property
  def project(self):
    raise NotImplementedError

  def _create_run(self, name, metadata):
    raise NotImplementedError

  def create_run(self, name=None, metadata=None):
    if name is None:
      name = get_default_name(self.project)
    run = self._create_run(name, metadata)
    self._on_run_created(run)
    return run
