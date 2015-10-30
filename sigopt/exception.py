import copy


class SigOptException(Exception):
  pass


class ApiException(SigOptException):
  def __init__(self, body, status_code):
    self.message = body.get('message', None) if body is not None else None
    self._body = body
    if self.message is not None:
      super(ApiException, self).__init__(self.message)
    else:
      super(ApiException, self).__init__()
    self.status_code = status_code

  def __repr__(self):
    return u'{0}({1}, {2}, {3})'.format(
      self.__class__.__name__,
      self.message,
      self.status_code,
      self._body,
    )

  def __str__(self):
    return '{0} ({1}): {2}'.format(
      self.__class__.__name__,
      self.status_code,
      self.message,
    )

  def to_json(self):
    return copy.deepcopy(self._body)
