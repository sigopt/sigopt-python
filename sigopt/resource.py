from .endpoint import BoundApiEndpoint

_NO_ARG = object()

class BoundApiResource(object):
  def __init__(self, resource, id, api_url):
    self._resource = resource
    self._id = id

    if id is _NO_ARG:
      self._base_url = api_url
    else:
      self._base_url = '{api_url}/{id}'.format(
        api_url=api_url,
        id=id,
      )

  def get_bound_entity(self, name):
    endpoint = self._resource._endpoints.get(name)
    if endpoint:
      return BoundApiEndpoint(self, endpoint)
    sub_resource = self._resource._sub_resources.get(name)
    if sub_resource:
      return PartiallyBoundApiResource(sub_resource, self)
    return None

  def __getattr__(self, attr):
    bound_entity = self.get_bound_entity(attr)
    if bound_entity:
      return bound_entity
    raise AttributeError(
        'Cannot find attribute `{attribute}` on resource `{resource}`, likely no endpoint exists for: '
        '{base_url}/{attribute}, or `{resource}` does not support `{attribute}`.'
      .format(
        attribute=attr,
        resource=self._resource._name,
        base_url=self._base_url,
      )
    )

class PartiallyBoundApiResource(object):
  def __init__(self, resource, bound_parent_resource):
    self._resource = resource
    self._bound_parent_resource = bound_parent_resource

  def __call__(self, id=_NO_ARG):
    api_url = '{parent_api_url}/{name}'.format(
      parent_api_url=self._bound_parent_resource._base_url,
      name=self._resource._name
    )
    return BoundApiResource(self._resource, id, api_url)

class BaseApiResource(object):
  def __init__(self, conn, name, version, endpoints=None, resources=None):
    self._conn = conn
    self._name = name
    self._version = version

    self._endpoints = dict((
      (endpoint._attribute_name, endpoint)
      for endpoint
      in endpoints
    )) if endpoints else {}

    self._sub_resources = dict((
      (resource._name, resource)
      for resource
      in resources
    )) if resources else {}

  def __call__(self, id=_NO_ARG):
    api_url = '{api_url}/{version}/{name}'.format(
      api_url=self._conn.api_url,
      version=self._version,
      name=self._name,
    )
    return BoundApiResource(self, id, api_url)

class ApiResource(BaseApiResource):
  def __init__(self, conn, name, endpoints=None, resources=None):
    super().__init__(
      conn=conn,
      name=name,
      version='v1',
      endpoints=endpoints,
      resources=resources,
    )
