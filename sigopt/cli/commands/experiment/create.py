from sigopt.logging import print_logger

from ...arguments import experiment_file_option, project_option
from ...utils import create_experiment_from_validated_data
from ..base import create_command


def print_start_worker_help(experiment):
  msg = f'''
You can now start workers for this experiment with the following CLI command:
> sigopt start-worker {experiment.id}

Or use the python client library:

  #/usr/bin/env python3
  import sigopt
  experiment = sigopt.get_experiment({experiment.id!r})
  for run in experiment.loop():
    with run:
      ...
'''
  print_logger.info(msg)

@create_command.command('experiment')
@experiment_file_option
@project_option
def create(experiment_file, project):
  '''Create a SigOpt Experiment.'''
  experiment = create_experiment_from_validated_data(experiment_file, project)
  print_start_worker_help(experiment)
