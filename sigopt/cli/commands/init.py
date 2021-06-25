import os

import click
import pkg_resources

from .base import sigopt_cli


def write_file(path, resource):
  if os.path.exists(path):
    if not os.path.isfile(path):
      raise click.ClickException(f"{path} already exists and is not a file.")
    should_write = click.prompt(
      f"{path} already exists. Replace it? (Y/n)",
      type=bool,
    )
  else:
    should_write = True
  if should_write:
    contents = pkg_resources.resource_string("sigopt.cli.resources", resource)
    with open(path, "wb") as fp:
      fp.write(contents)
      print(f"Wrote file contents for {path}")
  else:
    print(f"Skipping {path}")

@sigopt_cli.command()
def init():
  '''Initialize a directory for a SigOpt project.'''
  write_file("run.yml", "init_run.txt")
  write_file("experiment.yml", "init_experiment.txt")
  write_file("Dockerfile", "init_dockerfile.txt")
  write_file(".dockerignore", "init_dockerignore.txt")
