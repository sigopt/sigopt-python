from collections.abc import MutableMapping

from .lib import is_string


class RunParameters(MutableMapping):
  def __init__(self, run_context, fixed_items):
    self.__items = dict(fixed_items)
    self.__run_context = run_context
    self.__fixed_keys = set(fixed_items.keys())

  def update(self, other=(), /, **kwds):
    # this update is atomic, which reduces the number of calls to set_parameter(s)
    # the default implementation of update would result in a partial update if any of the setters failed
    # ex. (x := {}).update([(1, 2), ({}, 4)]) => raises TypeError and x == {1: 2}
    tmp = dict()
    tmp.update(other, **kwds)
    for key in tmp:
      self.__check_key_type(key)
    for key in tmp:
      self.__check_key_is_not_fixed(key)
    self.__items.update(tmp)
    self.__run_context.set_parameters(tmp)

  def __check_key_type(self, key):
    if not is_string(key):
      raise TypeError(f"parameter names must be strings, got {type(key).__name__!r}")

  def __check_key_is_not_fixed(self, key):
    if key in self.__fixed_keys:
      raise ValueError(f"value of {key!r} cannot be changed")

  def __getitem__(self, key):
    return self.__items[key]

  def __setitem__(self, key, value):
    self.__check_key_type(key)
    self.__check_key_is_not_fixed(key)
    rval = self.__items.__setitem__(key, value)
    self.__run_context.set_parameter(key, value)
    return rval

  def __delitem__(self, key):
    self.__check_key_is_not_fixed(key)
    rval = self.__items.__delitem__(key)
    self.__run_context.set_parameter(key, None)
    return rval

  def __iter__(self):
    return self.__items.__iter__()

  def __len__(self):
    return self.__items.__len__()

  def __repr__(self):
    return self.__items.__repr__()

  def __str__(self):
    return self.__items.__str__()


class GlobalRunParameters(MutableMapping):
  def __init__(self, global_run_context):
    self.__global_run_context = global_run_context
    self.__global_params = RunParameters(global_run_context, dict())

  @property
  def __params(self):
    run_context = self.__global_run_context.run_context
    if run_context is None:
      return self.__global_params
    return run_context.params

  def __getattribute__(self, attr):
    if attr.startswith("_"):
      return object.__getattribute__(self, attr)
    # delegate public (non-underscored) attributes to __params
    return getattr(self.__params, attr)

  def __dir__(self):
    return sorted(set(dir(super())) | set(dir(self.__params)))

  def __getitem__(self, key):
    return self.__params.__getitem__(key)

  def __setitem__(self, key, value):
    return self.__params.__setitem__(key, value)

  def __delitem__(self, key):
    return self.__params.__delitem__(key)

  def __iter__(self):
    return self.__params.__iter__()

  def __len__(self):
    return self.__params.__len__()

  def __repr__(self):
    return self.__params.__repr__()

  def __str__(self):
    return self.__params.__str__()
