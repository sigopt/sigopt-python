import copy
import simplejson
import requests
import warnings

from .exception import ApiException
from .objects import ApiObject
from .response import (
  ExperimentResponse, ClientResponse, UserResponse,
  ExperimentsBestObservationResponse, ExperimentsSuggestResponse, ExperimentsSuggestMultiResponse,
  ExperimentsWorkersResponse, ExperimentsHistoryResponse,
  ExperimentsAllocateResponse, ExperimentsCreateCohortResponse, ExperimentsUpdateCohortResponse,
  ClientsExperimentsResponse,
  UsersRolesResponse,
)

class BaseConnection(object):
  def __init__(self, client_token=None, user_token=None):
    self.api_url = 'https://api.sigopt.com'
    if client_token is None and user_token is None:
      raise ValueError('Must provide either user_token or client_token (or both)')

    self.client_token = client_token
    self.user_token = user_token


  def _handle_response(self, response):
    try:
      response_json = response.json()
    except simplejson.decoder.JSONDecodeError:
      raise ApiException({'message': response.text}, response.status_code)

    if 200 <= response.status_code <= 299:
      response = response_json.get('response')
      return response
    else:
      error_json = response_json.get('error', {})
      raise ApiException(error_json, response.status_code)

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
