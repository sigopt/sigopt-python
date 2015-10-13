import copy
import simplejson
import requests
import warnings

from ..endpoint import ApiEndpoint
from ..exception import ApiException
from ..interface import BaseConnection
from ..objects import ApiObject
from .resource import ApiResource
from ..response import (
  ExperimentResponse, ClientResponse, UserResponse,
  ExperimentsBestObservationResponse, ExperimentsSuggestResponse, ExperimentsSuggestMultiResponse,
  ExperimentsWorkersResponse, ExperimentsHistoryResponse,
  ExperimentsAllocateResponse, ExperimentsCreateCohortResponse, ExperimentsUpdateCohortResponse,
  ClientsExperimentsResponse,
  UsersRolesResponse,
)

class Connection(BaseConnection):
  def __init__(self, client_token=None, user_token=None, worker_id=None):
    super(Connection, self).__init__(client_token, user_token)

    self.worker_id = worker_id
    self.default_params = {
      'user_token': user_token,
      'client_token': client_token,
      'worker_id': worker_id,
    }

    self._experiments = ApiResource(
      self,
      'experiments',
      response_cls=ExperimentResponse,
      endpoints=[
        ApiEndpoint('allocate', ExperimentsAllocateResponse, 'GET'),
        ApiEndpoint('bestobservation', ExperimentsBestObservationResponse, 'GET'),
        ApiEndpoint('createcohort', ExperimentsCreateCohortResponse, 'POST'),
        ApiEndpoint('delete', None, 'POST'),
        ApiEndpoint('history', ExperimentsHistoryResponse, 'GET'),
        ApiEndpoint('releaseworker', None, 'POST'),
        ApiEndpoint('report', None, 'POST'),
        ApiEndpoint('reportmulti', None, 'POST'),
        ApiEndpoint('reset', None, 'POST'),
        ApiEndpoint('suggest', ExperimentsSuggestResponse, 'POST'),
        ApiEndpoint('suggestmulti', ExperimentsSuggestMultiResponse, 'POST'),
        ApiEndpoint('update', ExperimentResponse, 'POST'),
        ApiEndpoint('updatecohort', ExperimentsUpdateCohortResponse, 'POST'),
        ApiEndpoint('workers', ExperimentsWorkersResponse, 'GET'),
      ],
    )
    self._clients = ApiResource(
      self,
      'clients',
      response_cls=ClientResponse,
      endpoints=[
        ApiEndpoint('experiments', ClientsExperimentsResponse, 'GET'),
      ],
    )
    self._users = ApiResource(
      self,
      'users',
      response_cls=UserResponse,
      endpoints=[
        ApiEndpoint('roles', UsersRolesResponse, 'GET'),
      ],
    )

  @property
  def experiments(self):
    return self._experiments

  @property
  def clients(self):
    return self._clients

  @property
  def users(self):
    return self._users

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
    return self.experiments(experiment_id).report(data=data)

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

  def _ensure_client_token(self):
    if self.client_token is None:
      raise ValueError('client_token is required for this call')

  def _ensure_user_token(self):
    if self.user_token is None:
      raise ValueError('user_token is required for this call')

  def _request_params(self, params):
    req_params = copy.copy(self.default_params)
    req_params.update(params or {})

    def serialize(value):
      if isinstance(value, dict):
        return simplejson.dumps(value)
      return str(value)

    return dict((
      (key, serialize(self._to_api_value(value)))
      for key, value
      in req_params.items()
      if value is not None
    ))
