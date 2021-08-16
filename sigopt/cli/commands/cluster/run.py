import click

from ...arguments import dockerfile_option
from ..run_base import run_command
from .base import cluster_command


@cluster_command.command(context_settings=dict(
  allow_interspersed_args=False,
  ignore_unknown_options=True,
))
@click.pass_context
@dockerfile_option
@run_command
def run(ctx, command, run_options, dockerfile):
  '''Launch a SigOpt Run on the connected Kubernetes cluster.'''
  ctx.obj.controller.run_on_cluster(
    command=command,
    run_options=run_options,
    silent=False,
    dockerfile=dockerfile,
  )
