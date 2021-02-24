import warnings

from ..vendored import six

PROJECT_KEY = 'project'

EXPERIMENT_KEY = 'experiment'

VALID_TOP_LEVEL_KEYS = [
  EXPERIMENT_KEY,
]

FORBIDDEN_EXPERIMENT_KEYS = [
  PROJECT_KEY,
]

def validate_sigopt_input(sigopt_input, filename):
  if not isinstance(sigopt_input, dict):
    raise Exception(
      six.u('The {} file must be a mapping').format(filename)
    )
  invalid_top_level_keys = set(sigopt_input) - set(VALID_TOP_LEVEL_KEYS)
  if invalid_top_level_keys:
    warnings.warn(
      six.u('The following keys in {} are not recognized: {}').format(filename, list(invalid_top_level_keys)),
      RuntimeWarning,
    )
  return sigopt_input

def validate_experiment_input(experiment_input, filename):
  if not isinstance(experiment_input, dict):
    raise Exception(
      six.u('The "{}" section of {} must be a mapping').format(EXPERIMENT_KEY, filename)
    )
  if PROJECT_KEY in experiment_input:
    raise Exception(
      'The project field is not permitted in the experiment section.'
      ' Please set the SIGOPT_PROJECT environment variable instead.'
    )
  return experiment_input
