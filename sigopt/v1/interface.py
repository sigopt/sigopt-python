import copy
import simplejson
import requests
from requests.auth import HTTPBasicAuth
import warnings

from ..endpoint import ApiEndpoint
from ..exception import ApiException
from ..interface import BaseConnection
from ..objects import ApiObject, Observation, Experiment, Suggestion
from .resource import ApiResource

def ClassOrPaginatedClass(some_class):
  def decorator(body):
    if isinstance(body, list):
      return [
        some_class(data)
        for data
        in body
      ]
    else:
      return some_class(body)
  return decorator

@ClassOrPaginatedClass
def ObservationResponse(body):
  return Observation(body)

@ClassOrPaginatedClass
def SuggestionResponse(body):
  return Suggestion(body)

@ClassOrPaginatedClass
def ExperimentResponse(body):
  return Experiment(body)

class Connection(BaseConnection):
  def __init__(self, client_token, user_token=None):
    super(Connection, self).__init__(client_token, user_token)
    self.default_headers = {'Content-Type': 'application/json'}
    self.default_params = {}
    self.client_auth = HTTPBasicAuth(self.client_token, '')

    suggestions = ApiResource(
      self,
      'suggestions',
      response_cls=SuggestionResponse,
      endpoints=[
        ApiEndpoint('multi', SuggestionResponse, 'POST')
      ]
    )

    observations = ApiResource(
      self,
      'observations',
      response_cls=ObservationResponse,
      endpoints=[
        ApiEndpoint('multi', ObservationResponse, 'POST')
      ]
    )

    self._experiments = ApiResource(
      self,
      'experiments',
      response_cls=Experiment,
      resources=[
        suggestions,
        observations,
      ]
    )

  @property
  def experiments(self):
    return self._experiments

  def _get(self, url, params=None):
    request_params = self._request_params(params)
    return self._handle_response(requests.get(
      url,
      params=request_params,
      auth=self.client_auth,
      headers=self.default_headers,
    ))

  def _post(self, url, params=None):
    request_params = self._to_api_value(params)
    return self._handle_response(requests.post(
      url,
      json=request_params,
      auth=self.client_auth,
      headers=self.default_headers,
    ))

  def _put(self, url, params=None):
    request_params = self._to_api_value(params)
    return self._handle_response(requests.put(
      url,
      json=request_params,
      auth=self.client_auth,
      headers=self.default_headers,
    ))

  def _delete(self, url):
    return self._handle_response(requests.delete(
      url,
      auth=self.client_auth,
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
