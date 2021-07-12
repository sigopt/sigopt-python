from ...arguments import experiment_file_option
from ...utils import create_experiment_from_validated_data
from .base import experiment_command


@experiment_command.command()
@experiment_file_option
def create(experiment_file):
  '''Create a SigOpt Experiment.'''
  create_experiment_from_validated_data(experiment_file)
