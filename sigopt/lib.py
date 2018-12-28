import collections as _collections
import math as _math
import numbers as _numbers

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
    isinstance(val, _collections.Sequence) and
      not isinstance(val, _six.string_types) and
      not isinstance(val, _six.binary_type)
  )

def is_mapping(val):
  """
  Returns True iff this is a "dict-like" type
  """
  return isinstance(val, _collections.Mapping)

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
