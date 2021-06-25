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
