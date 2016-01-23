import copy
import simplejson
import warnings

from .endpoint import ApiEndpoint
from .exception import ApiException
from .objects import ApiObject
from .resource import ApiResource
from .requestor import Requestor
from .objects import (
  Client,
  Experiment,
  Observation,
  Pagination,
  Suggestion,
)

class Connection(object):
  def __init__(self, client_token):
    self.api_url = 'https://api.sigopt.com'
    if client_token is None:
      raise ValueError('Must provide client_token')

    self.client_token = client_token
    self.default_headers = {'Content-Type': 'application/json'}
    self.requestor = Requestor(self.client_token, '')

    suggestions = ApiResource(
      self,
      'suggestions',
      endpoints=[
        ApiEndpoint(None, Suggestion, 'POST', 'create'),
        ApiEndpoint(None, object_or_paginated_objects(Suggestion), 'GET', 'fetch'),
        ApiEndpoint(None, Suggestion, 'PUT', 'update'),
        ApiEndpoint(None, Suggestion, 'DELETE', 'delete'),
      ]
    )

    observations = ApiResource(
      self,
      'observations',
      endpoints=[
        ApiEndpoint(None, Observation, 'POST', 'create'),
        ApiEndpoint(None, object_or_paginated_objects(Observation), 'GET', 'fetch'),
        ApiEndpoint(None, Observation, 'PUT', 'update'),
        ApiEndpoint(None, Observation, 'DELETE', 'delete'),
      ]
    )

    self._experiments = ApiResource(
      self,
      'experiments',
      endpoints=[
        ApiEndpoint(None, Experiment, 'POST', 'create'),
        ApiEndpoint(None, object_or_paginated_objects(Experiment), 'GET', 'fetch'),
        ApiEndpoint(None, Experiment, 'PUT', 'update'),
        ApiEndpoint(None, Experiment, 'DELETE', 'delete'),
      ],
      resources=[
        suggestions,
        observations,
      ]
    )

    self._clients = ApiResource(
      self,
      'clients',
      endpoints=[
        ApiEndpoint(None, Client, 'GET', 'fetch'),
      ],
    )

  @property
  def clients(self):
    return self._clients

  @property
  def experiments(self):
    return self._experiments

  def _handle_response(self, response):
    try:
      response_json = response.json()
    except simplejson.decoder.JSONDecodeError:
      raise ApiException({'message': response.text}, response.status_code)

    if 200 <= response.status_code <= 299:
      return response_json
    else:
      raise ApiException(response_json, response.status_code)

  def _get(self, url, params=None):
    request_params = self._request_params(params)
    return self._handle_response(self.requestor.get(
      url,
      params=request_params,
      headers=self.default_headers,
    ))

  def _post(self, url, params=None):
    request_params = self._to_api_value(params)
    return self._handle_response(self.requestor.post(
      url,
      json=request_params,
      headers=self.default_headers,
    ))

  def _put(self, url, params=None):
    request_params = self._to_api_value(params)
    return self._handle_response(self.requestor.put(
      url,
      json=request_params,
      headers=self.default_headers,
    ))

  def _delete(self, url, params=None):
    request_params = self._to_api_value(params)
    return self._handle_response(self.requestor.delete(
      url,
      params=request_params,
      headers=self.default_headers,
    ))

  def _request_params(self, params):
    req_params = params or {}

    def serialize(value):
      if isinstance(value, dict) or isinstance(value, list):
        return simplejson.dumps(value)
      return str(value)

    return dict((
      (key, serialize(self._to_api_value(value)))
      for key, value
      in req_params.items()
      if value is not None
    ))

  def _to_api_value(self, obj):
    if isinstance(obj, ApiObject):
      return obj.to_json()
    elif isinstance(obj, dict):
      c = {}
      for key in obj:
        c[key] = self._to_api_value(obj[key])
      return c
    elif isinstance(obj, list):
      return [self._to_api_value(c) for c in obj]
    else:
      return obj


# Allows response to be a single object of class some_class or a paginated
# response of objects that come from class some_class
def object_or_paginated_objects(api_object):
  def decorator(body):
    if body.get('object') == 'pagination':
      return Pagination(api_object, body)
    else:
      return api_object(body)

  return decorator
