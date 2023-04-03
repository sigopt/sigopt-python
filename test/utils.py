# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import warnings
from contextlib import contextmanager


@contextmanager
def ObserveWarnings():
  with warnings.catch_warnings(record=True) as e:
    warnings.simplefilter("always")
    yield e
    warnings.simplefilter("error")
