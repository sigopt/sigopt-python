from sigopt.endpoint import ApiEndpoint, BoundApiEndpoint

class BoundApiResource(object):
  def __init__(self, resource, id):
    self.resource = resource
    self.id = id

  def fetch(self):
    fetch_endpoint = self.resource.endpoints[None]
    return BoundApiEndpoint(self, fetch_endpoint).__call__()

  def __getattr__(self, attr):
    endpoint = self.resource.endpoints.get(attr)
    if endpoint:
      return BoundApiEndpoint(self, endpoint)
    else:
      raise AttributeError(attr)


class ApiResource(object):
  def __init__(self, conn, name, response_cls, endpoints):
    self.conn = conn
    self.name = name
    self.response_cls = response_cls
    self.endpoints = dict((
      (endpoint.name, endpoint)
      for endpoint
      in endpoints + [ApiEndpoint(None, self.response_cls, 'GET')]
    ))

  def __call__(self, id):
    return BoundApiResource(self, id)

  def create(self, **kwargs):
    return self.response_cls(
      self.conn._post(self._base_url('create'), kwargs),
    )

  def _base_url(self, suffix):
    return '{api_url}/{api_version}/{name}/{suffix}'.format(
      api_url=self.conn.api_url,
      api_version=self.conn.api_version,
      name=self.name,
      suffix=suffix,
      )
