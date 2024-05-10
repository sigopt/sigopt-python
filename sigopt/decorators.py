# Copyright © 2024 Intel Corporation
#
# SPDX-License-Identifier: MIT


def public(f):
  """
    Indicates that the function or method is meant to be part of the public interface.
    Ie. intended to be used outside sigopt-python.
    """
  return f
