import click

from sigopt.config import config

from ..utils import setup_cli


@click.group()
def sigopt_cli():
  setup_cli(config)
