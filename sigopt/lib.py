import math as _math
import numbers as _numbers

try:
  from collections.abc import Mapping as _Mapping, Sequence as _Sequence
except ImportError:
  from collections import Mapping as _Mapping, Sequence as _Sequence

from .vendored import six as _six

def is_numpy_array(val):
  return val.__class__.__name__ == 'ndarray'

def is_sequence(val):
  """
  Returns True iff this is a "list-like" type.
  Avoids the common error that strings are iterable
  """
  if is_numpy_array(val):
    return True
  return (
    isinstance(val, _Sequence) and
      not isinstance(val, _six.string_types) and
      not isinstance(val, _six.binary_type)
  )

def is_mapping(val):
  """
  Returns True iff this is a "dict-like" type
  """
  return isinstance(val, _Mapping)

def is_integer(num):
  """
  Returns True iff this is an integer type. Avoids the common error that bools
  are instances of int, and handles numpy correctly
  """
  if isinstance(num, bool):
    return False
  if isinstance(num, _numbers.Integral):
    return True
  return False

def is_number(x):
  if isinstance(x, bool):
    return False
  if isinstance(x, float) and _math.isnan(x):
    return False
  return isinstance(x, _numbers.Number) or is_integer(x)

def is_string(s):
  return isinstance(s, _six.string_types)

def find(lis, predicate):
  """
  Finds the first element in lis satisfying predicate, or else None
  """
  return next((item for item in lis if predicate(item)), None)

def remove_nones(mapping):
  return {key: value for key, value in mapping.items() if value is not None}

def safe_format(string, *args, **kwargs):
  return string.format(*args, **kwargs)

def validate_name(warn, name):
  if not is_string(name):
    raise ValueError(f"The {warn} must be a string, not {type(name).__name__}")

def sanitize_number(warn, name, value):
  if is_integer(value):
    return value
  try:
    value = float(value)
    if _math.isinf(value) or _math.isnan(value):
      raise ValueError
    return value
  except (ValueError, TypeError):
    raise ValueError(f"The {warn} logged for `{name}` could not be converted to a number: {value!r}")
