from collections.abc import MutableMapping

from .lib import is_string


_get = object.__getattribute__
_set = object.__setattr__

class RunParameters(MutableMapping):
  def __init__(self, run_context, fixed_items):
    _set(self, "__items", dict(fixed_items))
    _set(self, "__run_context", run_context)
    _set(self, "__fixed_keys", set(fixed_items.keys()))

  def update(self, other=(), /, **kwds):  # pylint: disable=no-method-argument
    # this update is atomic, which reduces the number of calls to set_parameter(s)
    # the default implementation of update would result in a partial update if any of the setters failed
    # ex. (x := {}).update([(1, 2), ({}, 4)]) => raises TypeError and x == {1: 2}
    tmp = dict()
    tmp.update(other, **kwds)
    for key in tmp:
      self.__check_key_type(key)
    for key in tmp:
      self.__check_key_is_not_fixed(key)
    _get(self, "__items").update(tmp)
    _get(self, "__run_context").set_parameters(tmp)

  def __getattr__(self, attr):
    try:
      return self[attr]
    except KeyError:
      raise AttributeError(f"no parameter with name {attr!r}")

  def __setattr__(self, attr, value):
    try:
      self[attr] = value
    except KeyError as ke:
      raise AttributeError(str(ke))

  def __check_key_type(self, key):
    if not is_string(key):
      raise TypeError(f"parameter names must be strings, got {type(key).__name__!r}")

  def __check_key_is_not_fixed(self, key):
    if key in _get(self, "__fixed_keys"):
      raise ValueError(f"value of {key!r} cannot be changed")

  def __getitem__(self, key):
    return object.__getattribute__(self, "__items")[key]

  def __setitem__(self, key, value):
    self.__check_key_type(key)
    self.__check_key_is_not_fixed(key)
    _get(self, "__items")[key] = value
    _get(self, "__run_context").set_parameter(key, value)

  def __delitem__(self, key):
    self.__check_key_is_not_fixed(key)
    del _get(self, "__items")[key]
    _get(self, "__run_context").set_parameter(key, None)

  def __iter__(self):
    return iter(_get(self, "__items"))

  def __len__(self):
    return len(_get(self, "__items"))

  def __repr__(self):
    return repr(_get(self, "__items"))

  def __str__(self):
    return str(_get(self, "__items"))


class GlobalRunParameters(MutableMapping):
  def __init__(self, global_run_context):
    _set(self, "__global_run_context", global_run_context)
    _set(self, "__global_params", RunParameters(global_run_context, dict()))

  @property
  def __params(self):
    run_context = _get(self, "__global_run_context").run_context
    if run_context is None:
      return _get(self, "__global_params")
    return run_context.params

  def __getattribute__(self, attr):
    if attr.startswith("_"):
      try:
        return _get(self, attr)
      except AttributeError:
        pass
    params = self.__params
    return getattr(params, attr)

  def __setattr__(self, attr, value):
    params = self.__params
    setattr(params, attr, value)

  def __dir__(self):
    params = self.__params
    return sorted(set(dir(super())) | set(dir(params)))

  def __getitem__(self, key):
    params = self.__params
    return params[key]

  def __setitem__(self, key, value):
    params = self.__params
    params[key] = value

  def __delitem__(self, key):
    params = self.__params
    del params[key]

  def __iter__(self):
    params = self.__params
    return iter(params)

  def __len__(self):
    params = self.__params
    return len(params)

  def __repr__(self):
    params = self.__params
    return repr(params)

  def __str__(self):
    params = self.__params
    return str(params)
