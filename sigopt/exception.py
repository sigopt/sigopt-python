class SigOptException(Exception):
  pass


class ApiException(SigOptException):
  def __init__(self, body, status_code):
    self.message = body.get('message', None)
    self._body = body
    if self.message is not None:
      super(ApiException, self).__init__(self.message)
    else:
      super(ApiException, self).__init__()
    self.status_code = status_code

  def to_json(self):
    return self._body
