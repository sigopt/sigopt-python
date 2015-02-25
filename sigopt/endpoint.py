class BoundApiEndpoint(object):
  def __init__(self, bound_resource, endpoint):
    self._bound_resource = bound_resource
    self._endpoint = endpoint

  def __call__(self, **kwargs):
    name = self._endpoint._name
    url = self._bound_resource._resource._base_url(self._bound_resource._id) + ('/' + name if name else '')
    conn = self._bound_resource._resource._conn
    call = conn._get if self._endpoint._method == 'GET' else conn._post
    raw_response = call(url, kwargs)
    if self._endpoint._response_cls:
      return self._endpoint._response_cls(raw_response)
    else:
      return None


class ApiEndpoint(object):
  def __init__(self, name, response_cls, method):
    self._name = name
    self._response_cls = response_cls
    self._method = method
