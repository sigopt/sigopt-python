from sigopt.version import VERSION

from .base import sigopt_cli


@sigopt_cli.command()
def version():
  '''Show the installed SigOpt version.'''
  print(VERSION)
