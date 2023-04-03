# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
"""
Common utility functions for working with lists
"""
from .types import is_mapping, is_sequence, is_set


def list_get(lis, index):
  """
    Gets the list item at the provided index, or None if that index is invalid
    """
  try:
    return lis[index]
  except IndexError:
    return None


def remove_nones(lis):
  """
    Returns a copy of this object with all `None` values removed.
    """
  if is_mapping(lis):
    return {k: v for k, v in lis.items() if v is not None}
  if is_set(lis):
    return lis - {None}
  if is_sequence(lis):
    return [l for l in lis if l is not None]
  raise Exception(f"Unsupported type: {type(lis)}")


def coalesce(*args):
  """
    Returns the first non-None value, or None if no such value exists
    """
  return list_get(remove_nones(args), 0)


def partition(lis, predicate):
  """
    Splits a list into two lists based on a predicate. The first list will contain
    all elements of the provided list where predicate is true, and the second list
    will contain the rest
    """
  as_list = list(lis)
  true_list = []
  false_list = []
  for l in as_list:
    pred_value = predicate(l)
    if pred_value is True:
      true_list.append(l)
    elif pred_value is False:
      false_list.append(l)
    else:
      raise Exception("Invalid predicate")

  return true_list, false_list
