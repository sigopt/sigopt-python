from sigopt.endpoint import ApiEndpoint, BoundApiEndpoint

class BoundApiResource(object):
  def __init__(self, resource, id):
    self._resource = resource
    self._id = id

  def fetch(self):
    fetch_endpoint = self._resource._endpoints[None]
    return BoundApiEndpoint(self, fetch_endpoint).__call__()

  def __getattr__(self, attr):
    endpoint = self._resource._endpoints.get(attr)
    if endpoint:
      return BoundApiEndpoint(self, endpoint)
    else:
      raise AttributeError(attr)


class ApiResource(object):
  def __init__(self, conn, name, response_cls, endpoints):
    self._conn = conn
    self._name = name
    self._response_cls = response_cls
    self._endpoints = dict((
      (endpoint._name, endpoint)
      for endpoint
      in endpoints + [ApiEndpoint(None, self._response_cls, 'GET')]
    ))

  def __call__(self, id):
    return BoundApiResource(self, id)

  def create(self, **kwargs):
    return self._response_cls(
      self._conn._post(self._base_url('create'), kwargs),
    )

  def _base_url(self, suffix):
    return '{api_url}/v0/{name}/{suffix}'.format(
      api_url=self._conn.api_url,
      name=self._name,
      suffix=suffix,
      )
