from .endpoint import ApiEndpoint, BoundApiEndpoint

class BoundApiResource(object):
  def __init__(self, resource, id, api_url):
    self._resource = resource
    self._id = id

    if id is None:
      self._base_url = api_url
    else:
      self._base_url = '{api_url}/{id}'.format(
      api_url=api_url,
      id=id,
    )

  def __getattr__(self, attr):
    endpoint = self._resource._endpoints.get(attr)
    if endpoint:
      return BoundApiEndpoint(self, endpoint)
    else:
      sub_resource = self._resource._sub_resources.get(attr)
      if sub_resource:
        return PartiallyBoundApiResource(sub_resource, self)
    raise AttributeError(attr)

class PartiallyBoundApiResource(object):
  def __init__(self, resource, bound_parent_resource):
    self._resource = resource
    self._bound_parent_resource = bound_parent_resource

  def __call__(self, id=None):
    api_url = '{parent_api_url}/{name}'.format(
      parent_api_url=self._bound_parent_resource._base_url,
      name=self._resource._name
    )
    return BoundApiResource(self._resource, id, api_url)

class BaseApiResource(object):
  def __init__(self, conn, name, response_cls, version, endpoints=None, resources=None):
    self._conn = conn
    self._name = name
    self._response_cls = response_cls
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

  def __call__(self, id=None):
    api_url = '{api_url}/{version}/{name}'.format(
      api_url=self._conn.api_url,
      version=self._version,
      name=self._name,
    )
    return BoundApiResource(self, id, api_url)