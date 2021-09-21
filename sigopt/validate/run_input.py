from sigopt.lib import validate_name, is_string, is_mapping, is_sequence

from .common import validate_top_level_dict
from .exceptions import ValidationError


def validate_run_input(run_input):
  run_input = validate_top_level_dict(run_input)
  validated = {}
  name = run_input.get("name")
  if name is not None:
    try:
      validate_name("run name", name)
    except ValueError as ve:
      raise ValidationError(str(ve)) from ve
  validated["name"] = name
  args = run_input.get("run")
  if args is None:
    args = []
  elif is_string(args):
    args = ["sh", "-c", args]
  elif is_sequence(args):
    args = list(args)
    for arg in args:
      if not is_string(arg):
        raise ValidationError("'run' has some non-string arguments")
  else:
    raise ValidationError("'run' must be a command string or list of command arguments")
  validated["run"] = args
  image = run_input.get("image")
  if image is not None:
    try:
      validate_name("run image", image)
    except ValueError as ve:
      raise ValidationError(str(ve)) from ve
    validated["image"] = image
  resources = run_input.get("resources")
  if resources is None:
    resources = {}
  else:
    if not is_mapping(resources):
      raise ValidationError("'resources' must be a mapping of key strings to values")
    for key in resources:
      if not is_string(key):
        raise ValidationError("'resources' can only have string keys")
  validated["resources"] = resources
  unknown_keys = set(run_input) - set(validated)
  if unknown_keys:
    joined_keys = ", ".join(unknown_keys)
    raise ValidationError(f"unknown run options: {joined_keys}")
  return validated
