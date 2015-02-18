import json
import requests

from sigopt.exception import ApiException
from sigopt.objects import ApiObject
from sigopt.response import ExperimentsCreateResponse, ExperimentsSuggestResponse

class Connection(object):
  def __init__(self, client_token=None, user_token=None, worker_id=None):
    self.api_url = 'https://api.sigopt.com'
    self.api_version = 'v0'
    if client_token is None and user_token is None:
      raise ValueError('Must provide either user_token or client_token (or both)')

    self.client_token = client_token
    self.user_token = user_token
    self.worker_id = worker_id

  def experiment_create(self, client_id, data):
    self._ensure_user_token()
    url = self._base_url('create')
    response = self._handle_response(requests.post(url, data={
      'user_token': self.user_token,
      'data': json.dumps(self._to_api_json(data)),
      'client_id': client_id,
    }))
    return ExperimentsCreateResponse(response)

  def experiment_report(self, experiment_id, data):
    self._ensure_client_token()
    url = self._base_url(experiment_id) + '/report'
    self._handle_response(requests.post(url, data={
      'client_token': self.client_token,
      'data': json.dumps(self._to_api_json(data)),
      'worker_id': self.worker_id,
    }))
    return None

  def experiment_suggest(self, experiment_id):
    self._ensure_client_token()
    url = self._base_url(experiment_id) + '/suggest'
    response = self._handle_response(requests.post(url, data={
      'client_token': self.client_token,
      'worker_id': self.worker_id,
    }))
    return ExperimentsSuggestResponse(response)

  def _base_url(self, experiment_id):
    return '{api_url}/{api_version}/experiments/{experiment_id}'.format(
      api_url=self.api_url,
      api_version=self.api_version,
      experiment_id=experiment_id,
      )

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

  def _to_api_json(self, obj):
    if isinstance(obj, ApiObject):
      return obj.to_json()
    elif isinstance(obj, dict):
      c = {}
      for key in obj:
        c[key] = self._to_api_json(obj[key])
      return c
    elif isinstance(obj, list):
      return [self._to_api_json(c) for c in obj]
    else:
      return obj
