import click

from sigopt.validate import validate_run_input

from .load_yaml import load_yaml_callback


run_file_option = click.option(
  '-r',
  '--run-file',
  default='run.yml',
  type=click.Path(),
  callback=load_yaml_callback(validate_run_input, ignore_no_file=True),
)
