class SigOptException(Exception):
  pass


class ApiException(SigOptException):
  def __init__(self, message, status_code):
    if message is not None:
      super(ApiException, self).__init__(message)
    else:
      super(ApiException, self).__init__()
    self.status_code = status_code
