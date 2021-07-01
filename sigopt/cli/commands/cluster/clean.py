import click

from .base import cluster_command


@cluster_command.command()
@click.pass_context
def clean(ctx):
  '''Reclaim space for building models.'''
  ctx.obj.controller.clean_images()
