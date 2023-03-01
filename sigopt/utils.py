# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import contextlib
from http import HTTPStatus

from sigopt.exception import ApiException

class HandledException:
  def __init__(self):
    self.exception = None

@contextlib.contextmanager
def accept_sigopt_not_found():
  handled = HandledException()
  try:
    yield handled
  except ApiException as ae:
    if ae.status_code != HTTPStatus.NOT_FOUND:
      raise
    handled.exception = ae

def batcher(alist, n=1):
  l = len(alist)
  for ndx in range(0, l, n):
    yield alist[ndx:min(ndx + n, l)]
