import copy
from .vendored import six


class SigOptException(Exception):
  pass


@six.python_2_unicode_compatible
class ConnectionException(SigOptException):
  """
  An exception that occurs when the SigOpt API was unavailable.
  """
  def __init__(self, message):
    super().__init__(message)
    self.message = message

  def __str__(self):
    return six.u('{0}: {1}').format(
      'ConnectionException',
      self.message if self.message is not None else '',
    )

@six.python_2_unicode_compatible
class ApiException(SigOptException):
  """
  An exception that occurs when the SigOpt API was contacted successfully, but
  it responded with an error.
  """
  def __init__(self, body, status_code):
    self.message = body.get('message', None) if body is not None else None
    self._body = body
    if self.message is not None:
      super().__init__(self.message)
    else:
      super().__init__()
    self.status_code = status_code

  def __str__(self):
    return six.u('{0} ({1}): {2}').format(
      'ApiException',
      self.status_code,
      self.message if self.message is not None else '',
    )

  def to_json(self):
    return copy.deepcopy(self._body)

class RunException(SigOptException):
  pass
