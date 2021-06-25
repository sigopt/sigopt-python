from functools import cached_property

import click

from sigopt.orchestrate.controller import OrchestrateController

from ..base import sigopt_cli


class Context:
  @cached_property
  def controller(self):
    return OrchestrateController.create()

@sigopt_cli.group("cluster")
@click.pass_context
def cluster_command(ctx):
  '''Commands for running SigOpt on Kubernetes clusters.'''
  ctx.obj = Context()
