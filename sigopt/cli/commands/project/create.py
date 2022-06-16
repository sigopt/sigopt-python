import click

from sigopt.exception import ConflictingProjectException
from sigopt.factory import SigOptFactory
from sigopt.sigopt_logging import print_logger

from ...arguments import project_option, project_name_option
from ..base import create_command

@create_command.command('project')
@project_option
@project_name_option
def create(project, project_name):
  '''Create a SigOpt Project.'''
  factory = SigOptFactory(project)
  try:
    factory.create_project(project_name)
  except ConflictingProjectException as cpe:
    raise click.ClickException(cpe) from cpe
  print_logger.info("Project '%s' created.", project)
