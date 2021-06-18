from collections.abc import MutableMapping

from .lib import is_string


class RunParameters(MutableMapping):
  def __init__(self, run_context, fixed_items):
    self.__items = dict(fixed_items)
    self.__run_context = run_context
    self.__fixed_keys = set(fixed_items.keys())

  def __check_key_is_not_fixed(self, key):
    if key in self.__fixed_keys:
      raise ValueError(f"The value of {repr(key)} cannot be changed")

  def __getitem__(self, key):
    return self.__items[key]

  def __setitem__(self, key, value):
    if not is_string(key):
      raise KeyError("Parameter names must be strings")
    self.__check_key_is_not_fixed(key)
    self.__run_context.set_parameter(key, value)
    return self.__items.__setitem__(key, value)

  def __delitem__(self, key):
    self.__check_key_is_not_fixed(key)
    self.__run_context.set_parameter(key, None)
    return self.__items.__delitem__(key)

  def __iter__(self):
    return self.__items.__iter__()

  def __len__(self):
    return self.__items.__len__()

  def __repr__(self):
    return self.__items.__repr__()

  def __str__(self):
    return self.__items.__str__()
