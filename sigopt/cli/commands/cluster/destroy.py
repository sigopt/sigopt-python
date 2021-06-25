import click

from .base import cluster_command


@cluster_command.command()
@click.pass_context
def destroy(ctx):
  '''Destroy the connected Kubernetes cluster.'''
  ctx.obj.controller.destroy_connected_cluster()
