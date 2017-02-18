from .compat import json as simplejson

class BoundApiEndpoint(object):
  def __init__(self, bound_resource, endpoint):
    self._bound_resource = bound_resource
    self._endpoint = endpoint

  def call_with_json(self, json):
    return self.call_with_params(simplejson.loads(json))

  def call_with_params(self, params):
    name = self._endpoint._name
    url = self._bound_resource._base_url + ('/' + name if name else '')
    conn = self._bound_resource._resource._conn
    raw_response = None

    call = None
    if self._endpoint._method == 'GET':
      call = conn._get
    elif self._endpoint._method == 'POST':
      call = conn._post
    elif self._endpoint._method == 'PUT':
      call = conn._put
    elif self._endpoint._method == 'DELETE':
      call = conn._delete

    raw_response = call(url, params)

    if self._endpoint._response_cls is not None:
      return self._endpoint._response_cls(raw_response, self, params)
    else:
      return None

  def __call__(self, **kwargs):
    return self.call_with_params(kwargs)


class ApiEndpoint(object):
  def __init__(self, name, response_cls, method, attribute_name=None):
    self._name = name
    self._response_cls = response_cls
    self._method = method
    self._attribute_name = attribute_name or name
