# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from sigopt.orchestrate.controller import OrchestrateController

from ..base import sigopt_cli


class Context:
  _controller = None

  @property
  def controller(self):
    if self._controller is None:
      self._controller = OrchestrateController.create()
    return self._controller

@sigopt_cli.group("cluster")
@click.pass_context
def cluster_command(ctx):
  '''Commands for running SigOpt on Kubernetes clusters.'''
  ctx.obj = Context()
