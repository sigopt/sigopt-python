import json
import logging
import requests

from sigopt.exception import ApiException
from sigopt.response import ReportResponse, SuggestResponse

class Connection(object):
  def __init__(self, client_token, experiment_id, worker_id=None):
    self.api_url = 'https://api.sigopt.com'
    self.api_version = 'v0'
    self.client_token = client_token
    self.experiment_id = experiment_id
    self.worker_id = worker_id
    self.logger = logging.getLogger(__name__)

  def report(self, data):
    url = self._base_url + '/report'
    request_data = {
      'client_token': self.client_token,
      'data': json.dumps(data),
      'worker_id': self.worker_id,
    }

    response = self._handle_response(requests.post(url, data=request_data))
    return ReportResponse(response)

  def suggest(self):
    url = self._base_url + '/suggest'
    request_data = {
      'client_token': self.client_token,
      'worker_id': self.worker_id,
    }

    response = self._handle_response(requests.post(url, data=request_data))
    return SuggestResponse(response)

  @property
  def _base_url(self):
    return '{api_url}/{api_version}/experiments/{experiment_id}'.format(
      api_url=self.api_url,
      api_version=self.api_version,
      experiment_id=self.experiment_id,
      )

  def _handle_response(self, response):
    response_json = response.json()
    if 200 <= response.status_code <= 299:
      response = response_json.get('response')
      warnings = response.get('warnings', [])
      for warning in warnings:
        self._logger.warn(warning)
      return response
    else:
      error_message = response_json.get('error', {}).get('message', None)
      raise ApiException(error_message, response.status_code)
