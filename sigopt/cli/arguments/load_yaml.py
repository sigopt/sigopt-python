import errno

import click
import yaml

from sigopt.validate import ValidationError


class ValidatedData:
  def __init__(self, filename, validated_data):
    self.filename = filename
    self.data = validated_data

def load_yaml(filename, validator, ignore_no_file):
  if filename is None:
    return None
  try:
    with open(filename) as yaml_fp:
      data = yaml.safe_load(yaml_fp)
  except OSError as ose:
    if ose.errno == errno.ENOENT and ignore_no_file:
      return None
    raise click.BadParameter(f'Could not open {filename}: {ose}') from ose
  except (yaml.parser.ParserError, yaml.scanner.ScannerError) as pe:
    raise click.BadParameter(f'Could not parse {filename}: {pe}') from pe

  try:
    validated_data = validator(data)
  except ValidationError as ve:
    raise click.BadParameter(f'Bad format in {filename}: {ve}') from ve

  return ValidatedData(filename, validated_data)

def load_yaml_callback(validator, ignore_no_file=False):
  return lambda ctx, p, value: load_yaml(value, validator, ignore_no_file=ignore_no_file)
