# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from collections.abc import MutableMapping

from .lib import is_string


_get = object.__getattribute__
_set = object.__setattr__

class RunParameters(MutableMapping):
  def __init__(self, run_context, fixed_items, default_items=None):
    if default_items:
      items = dict(default_items)
      items.update(fixed_items)
    else:
      items = dict(fixed_items)
    _set(self, "__items", items)
    _set(self, "__run_context", run_context)
    _set(self, "__fixed_keys", set(fixed_items.keys()))

  def update(self, *args, **kwds):  # pylint: disable=arguments-differ
    # this update is atomic, which reduces the number of calls to set_parameter(s)
    # the default implementation of update would result in a partial update if any of the setters failed
    # ex. (x := {}).update([(1, 2), ({}, 4)]) => raises TypeError and x == {1: 2}
    tmp = dict()
    tmp.update(*args, **kwds)
    self.__check_dict_for_update(tmp, check_fixed=True)
    _get(self, "__items").update(tmp)
    _get(self, "__run_context").set_parameters(tmp)

  def setdefaults(self, *args, **kwds):
    tmp = dict()
    tmp.update(*args, **kwds)
    self.__check_dict_for_update(tmp, check_fixed=False)
    items = _get(self, "__items")
    unset_keys = set(tmp) - set(items)
    update = {key: tmp[key] for key in unset_keys}
    items.update(update)
    _get(self, "__run_context").set_parameters(update)
    return self

  def __getattr__(self, attr):
    try:
      return self[attr]
    except KeyError as ke:
      raise AttributeError(f"no parameter with name {attr!r}") from ke

  def __setattr__(self, attr, value):
    try:
      self[attr] = value
    except KeyError as ke:
      raise AttributeError(str(ke)) from ke

  def __check_key_type(self, key):
    if not is_string(key):
      raise TypeError(f"parameter names must be strings, got {type(key).__name__!r}")

  def __check_key_is_not_fixed(self, key):
    if key in _get(self, "__fixed_keys"):
      raise ValueError(f"value of {key!r} cannot be changed")

  def __check_dict_for_update(self, update_dict, check_fixed):
    for key in update_dict:
      self.__check_key_type(key)
    if check_fixed:
      for key in update_dict:
        self.__check_key_is_not_fixed(key)

  def __getitem__(self, key):
    return _get(self, "__items")[key]

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
    # public methods like update and pop should pass to the underlying __params,
    # but attributes beginning with "_" should at least attempt to be resolved.
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
