import json
import requests
import warnings

from sigopt.endpoint import ApiEndpoint
from sigopt.exception import ApiException
from sigopt.objects import ApiObject
from sigopt.resource import ApiResource
from sigopt.response import (
  ExperimentResponse, ClientResponse,
  ExperimentsSuggestResponse, ClientsExperimentsResponse,
)

class Connection(object):
  def __init__(self, client_token=None, user_token=None, worker_id=None):
    self.api_url = 'https://api.sigopt.com'
    self.api_version = 'v0'
    if client_token is None and user_token is None:
      raise ValueError('Must provide either user_token or client_token (or both)')

    self.client_token = client_token
    self.user_token = user_token
    self.worker_id = worker_id

    self.experiments = ApiResource(
      self,
      'experiments',
      response_cls=ExperimentResponse,
      endpoints=[
        ApiEndpoint('suggest', ExperimentsSuggestResponse, 'POST'),
        ApiEndpoint('report', None, 'POST'),
        ApiEndpoint('delete', None, 'POST'),
      ],
    )
    self.clients = ApiResource(
      self,
      'clients',
      response_cls=ClientResponse,
      endpoints=[
        ApiEndpoint('experiments', ClientsExperimentsResponse, 'GET'),
      ],
    )

  def experiment(self, experiment_id):
    warnings.warn('This method will be removed in version 1.0', DeprecationWarning, stacklevel=2)
    self._ensure_user_token()
    return self.experiments(experiment_id)

  def experiment_create(self, client_id, data):
    warnings.warn('This method will be removed in version 1.0', DeprecationWarning, stacklevel=2)
    self._ensure_user_token()
    return self.experiments.create(client_id=client_id, data=data)

  def experiment_delete(self, experiment_id):
    warnings.warn('This method will be removed in version 1.0', DeprecationWarning, stacklevel=2)
    self._ensure_user_token()
    return self.experiments(experiment_id).delete()

  def experiment_report(self, experiment_id, data):
    warnings.warn('This method will be removed in version 1.0', DeprecationWarning, stacklevel=2)
    self._ensure_client_token()
    return self.experiments(experiment_id).report({
      'data': data,
    })

  def client_experiments(self, client_id):
    warnings.warn('This method will be removed in version 1.0', DeprecationWarning, stacklevel=2)
    self._ensure_user_token()
    return self.clients(client_id).experiments()

  def experiment_suggest(self, experiment_id):
    warnings.warn('This method will be removed in version 1.0', DeprecationWarning, stacklevel=2)
    self._ensure_client_token()
    return self.experiments(experiment_id).suggest()

  def _get(self, url, params=None):
    request_params = self._request_params(params)
    return self._handle_response(requests.get(url, params=request_params))

  def _post(self, url, params=None):
    request_params = self._request_params(params)
    return self._handle_response(requests.post(url, data=request_params))

  def _handle_response(self, response):
    response_json = response.json()
    if 200 <= response.status_code <= 299:
      response = response_json.get('response')
      return response
    else:
      error_message = response_json.get('error', {}).get('message', None)
      raise ApiException(error_message, response.status_code)

  def _ensure_client_token(self):
    if self.client_token is None:
      raise ValueError('client_token is required for this call')

  def _ensure_user_token(self):
    if self.user_token is None:
      raise ValueError('user_token is required for this call')

  def _request_params(self, params):
    ret = {
      'user_token': self.user_token,
      'client_token': self.client_token,
      'worker_id': self.worker_id,
    }
    ret.update(params or {})

    def serialize(value):
      if isinstance(value, dict):
        return json.dumps(value)
      return str(value)

    return dict(((key, serialize(self._to_api_value(value))) for key, value in ret.iteritems()))

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
