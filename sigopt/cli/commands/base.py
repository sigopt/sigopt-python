import click
from sigopt.config import config
from ..utils import setup_cli


@click.group()
def sigopt_cli():
  setup_cli(config)


@sigopt_cli.group("create")
def create_command():
  '''Commands for create SigOpt Objects.'''


@sigopt_cli.group("archive")
def archive_command():
  '''Commands for archive SigOpt Objects.'''


@sigopt_cli.group("unarchive")
def unarchive_command():
  '''Commands for unarchive SigOpt Objects.'''
