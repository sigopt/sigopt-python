import os
import warnings

import requests
from requests.adapters import HTTPAdapter

from .compat import json as simplejson
from .config import config
from .endpoint import ApiEndpoint
from .objects import (
  ApiObject,
  BestAssignments,
  Checkpoint,
  Client,
  Experiment,
  Importances,
  MetricImportances,
  Observation,
  Organization,
  Pagination,
  Project,
  QueuedSuggestion,
  Session,
  StoppingCriteria,
  Suggestion,
  Token,
  TrainingRun,
)
from .requestor import Requestor, DEFAULT_API_URL
from .resource import ApiResource
from .urllib3_patch import ExpiringHTTPConnectionPool, ExpiringHTTPSConnectionPool
from .version import VERSION


def get_expiring_session():
  adapter = HTTPAdapter()
  adapter.poolmanager.pool_classes_by_scheme = {
    "http": ExpiringHTTPConnectionPool,
    "https": ExpiringHTTPSConnectionPool,
  }
  session = requests.Session()
  session.mount("http://", adapter)
  session.mount("https://", adapter)
  return session

class ConnectionImpl(object):
  def __init__(self, requestor, api_url=None, user_agent=None, verify_ssl_certs=None):
    self.requestor = requestor
    self.api_url = api_url or DEFAULT_API_URL

    suggestions = ApiResource(
      self,
      'suggestions',
      endpoints=[
        ApiEndpoint(None, Suggestion, 'POST', 'create'),
        ApiEndpoint(None, object_or_paginated_objects(Suggestion), 'GET', 'fetch'),
        ApiEndpoint(None, Suggestion, 'PUT', 'update'),
        ApiEndpoint(None, None, 'DELETE', 'delete'),
      ],
    )

    queued_suggestions = ApiResource(
      self,
      'queued_suggestions',
      endpoints=[
        ApiEndpoint(None, QueuedSuggestion, 'POST', 'create'),
        ApiEndpoint(None, object_or_paginated_objects(QueuedSuggestion), 'GET', 'fetch'),
        ApiEndpoint(None, None, 'DELETE', 'delete'),
      ]
    )

    observations = ApiResource(
      self,
      'observations',
      endpoints=[
        ApiEndpoint('batch', paginated_objects(Observation), 'POST', 'create_batch'),
        ApiEndpoint(None, Observation, 'POST', 'create'),
        ApiEndpoint(None, object_or_paginated_objects(Observation), 'GET', 'fetch'),
        ApiEndpoint(None, Observation, 'PUT', 'update'),
        ApiEndpoint(None, None, 'DELETE', 'delete'),
      ],
    )

    best_assignments = ApiResource(
      self,
      'best_assignments',
      endpoints=[
        ApiEndpoint(None, object_or_paginated_objects(BestAssignments), 'GET', 'fetch'),
      ],
    )

    best_training_runs = ApiResource(
      self,
      'best_training_runs',
      endpoints=[
        ApiEndpoint(None, paginated_objects(TrainingRun), 'GET', 'fetch'),
      ],
    )

    importances = ApiResource(
      self,
      'importances',
      endpoints=[
        ApiEndpoint(None, Importances, 'GET', 'fetch'),
      ],
    )

    metric_importances = ApiResource(
      self,
      'metric_importances',
      endpoints=[
        ApiEndpoint(None, paginated_objects(MetricImportances), 'GET', 'fetch'),
      ],
    )

    stopping_criteria = ApiResource(
      self,
      'stopping_criteria',
      endpoints=[
        ApiEndpoint(None, StoppingCriteria, 'GET', 'fetch'),
      ],
    )

    checkpoints = ApiResource(
      self,
      'checkpoints',
      endpoints=[
        ApiEndpoint(None, Checkpoint, 'POST', 'create'),
        ApiEndpoint(None, object_or_paginated_objects(Checkpoint), 'GET', 'fetch')
      ]
    )

    experiment_training_runs = ApiResource(
      self,
      'training_runs',
      endpoints=[
        ApiEndpoint(None, TrainingRun, 'POST', 'create'),
        ApiEndpoint(None, object_or_paginated_objects(TrainingRun), 'GET', 'fetch'),
        ApiEndpoint(None, TrainingRun, 'PUT', 'update'),
        ApiEndpoint(None, None, 'DELETE', 'delete'),
      ],
      resources=[checkpoints],
    )

    experiment_tokens = ApiResource(
      self,
      'tokens',
      endpoints=[
        ApiEndpoint(None, Token, 'POST', 'create'),
      ],
    )

    self.tokens = ApiResource(
      self,
      'tokens',
      endpoints=[
        ApiEndpoint(None, Token, 'GET', 'fetch'),
      ],
    )

    self.experiments = ApiResource(
      self,
      'experiments',
      endpoints=[
        ApiEndpoint(None, Experiment, 'POST', 'create'),
        ApiEndpoint(None, object_or_paginated_objects(Experiment), 'GET', 'fetch'),
        ApiEndpoint(None, Experiment, 'PUT', 'update'),
        ApiEndpoint(None, None, 'DELETE', 'delete'),
      ],
      resources=[
        best_assignments,
        best_training_runs,
        experiment_tokens,
        experiment_training_runs,
        importances,
        metric_importances,
        observations,
        queued_suggestions,
        stopping_criteria,
        suggestions,
      ],
    )

    client_experiments = ApiResource(
      self,
      'experiments',
      endpoints=[
        ApiEndpoint(None, Experiment, 'POST', 'create'),
        ApiEndpoint(None, paginated_objects(Experiment), 'GET', 'fetch'),
      ],
    )

    client_project_experiments = ApiResource(
      self,
      'experiments',
      endpoints=[
        ApiEndpoint(None, paginated_objects(Experiment), 'GET', 'fetch'),
      ],
    )

    client_project_training_runs = ApiResource(
      self,
      'training_runs',
      endpoints=[
        ApiEndpoint(None, paginated_objects(TrainingRun), 'GET', 'fetch'),
        ApiEndpoint(None, TrainingRun, 'POST', 'create'),
      ],
      resources=[checkpoints],
    )

    client_projects = ApiResource(
      self,
      'projects',
      endpoints=[
        ApiEndpoint(None, Project, 'POST', 'create'),
        ApiEndpoint(None, object_or_paginated_objects(Project), 'GET', 'fetch'),
        ApiEndpoint(None, Project, 'PUT', 'update'),
      ],
      resources=[
        client_project_experiments,
        client_project_training_runs,
      ],
    )

    self.training_runs = ApiResource(
      self,
      'training_runs',
      endpoints=[
        ApiEndpoint(None, object_or_paginated_objects(TrainingRun), 'GET', 'fetch'),
        ApiEndpoint(None, TrainingRun, 'PUT', 'update'),
        ApiEndpoint(None, None, 'DELETE', 'delete'),
      ],
      resources=[checkpoints]
    )

    self.clients = ApiResource(
      self,
      'clients',
      endpoints=[
        ApiEndpoint(None, Client, 'GET', 'fetch'),
      ],
      resources=[
        client_experiments,
        client_projects,
      ],
    )

    self.organizations = ApiResource(
      self,
      'organizations',
      endpoints=[
        ApiEndpoint(None, object_or_paginated_objects(Organization), 'GET', 'fetch'),
      ],
    )

    self.user_agent = user_agent
    if verify_ssl_certs is not None:
      self.set_verify_ssl_certs(verify_ssl_certs)

    self.pki_sessions = ApiResource(
      self,
      'pki_sessions',
      endpoints=[
        ApiEndpoint(None, Session, 'POST', 'create'),
      ],
    )

  def _request(self, method, url, params, headers=None):
    if method.upper() in ('GET', 'DELETE'):
      json, params = None, self._request_params(params)
    else:
      json, params = ApiObject.as_json(params), None

    return self.requestor.request(
      method,
      url,
      json=json,
      params=params,
      headers=headers,
      user_agent=self.user_agent,
    )

  def _get(self, url, params=None):
    return self._request('GET', url, params)

  def _post(self, url, params=None):
    return self._request('POST', url, params)

  def _put(self, url, params=None):
    return self._request('PUT', url, params)

  def _delete(self, url, params=None):
    return self._request('DELETE', url, params)

  def _request_params(self, params):
    req_params = params or {}

    def serialize(value):
      if isinstance(value, (dict, list)):
        return simplejson.dumps(value)
      return str(value)

    return dict((
      (key, serialize(ApiObject.as_json(value)))
      for key, value
      in req_params.items()
      if value is not None
    ))

  def set_api_url(self, api_url):
    self.api_url = api_url

  def set_verify_ssl_certs(self, verify_ssl_certs):
    self.requestor.verify_ssl_certs = verify_ssl_certs

  def set_proxies(self, proxies):
    self.requestor.proxies = proxies

  def set_timeout(self, timeout):
    self.requestor.timeout = timeout

  def set_client_ssl_certs(self, client_ssl_certs):
    self.requestor.client_ssl_certs = client_ssl_certs

  def set_client_token(self, client_token):
    self.requestor.set_client_token(client_token)


class Connection(object):
  """
  Client-facing interface for creating Connections.
  Shouldn't be changed without a major version change.
  """
  def __init__(self, client_token=None, user_agent=None, session=None, _show_deprecation_warning=True):
    if _show_deprecation_warning:
      warnings.warn(
        "You're currently using the old SigOpt Experience."
        " Try out the new and improved SigOpt experience by getting started with the docs today."
        " You have until July 2022 to migrate over without experiencing breaking changes.",
        UserWarning,
      )
    client_token = client_token or os.environ.get('SIGOPT_API_TOKEN', config.api_token)
    api_url = os.environ.get('SIGOPT_API_URL') or DEFAULT_API_URL
    # no-verify overrides a passed in path
    no_verify_ssl_certs = os.environ.get('SIGOPT_API_NO_VERIFY_SSL_CERTS')
    if no_verify_ssl_certs:
      verify_ssl_certs = False
    else:
      verify_ssl_certs = os.environ.get('SIGOPT_API_VERIFY_SSL_CERTS')

    if not client_token:
      raise ValueError('Must provide client_token or set environment variable SIGOPT_API_TOKEN')

    default_headers = {
      'Content-Type': 'application/json',
      'X-SigOpt-Python-Version': VERSION,
    }
    if session is None:
      session = get_expiring_session()
    requestor = Requestor(
      client_token,
      '',
      default_headers,
      session=session,
    )
    self.impl = ConnectionImpl(requestor, api_url=api_url, user_agent=user_agent, verify_ssl_certs=verify_ssl_certs)

  def set_api_url(self, api_url):
    self.impl.set_api_url(api_url)

  def set_verify_ssl_certs(self, verify_ssl_certs):
    self.impl.set_verify_ssl_certs(verify_ssl_certs)

  def set_proxies(self, proxies):
    self.impl.set_proxies(proxies)

  def set_timeout(self, timeout):
    self.impl.set_timeout(timeout)

  def set_client_ssl_certs(self, client_ssl_certs):
    self.impl.set_client_ssl_certs(client_ssl_certs)

  def set_client_token(self, client_token):
    self.impl.set_client_token(client_token)

  @property
  def clients(self):
    return self.impl.clients

  @property
  def experiments(self):
    return self.impl.experiments

  @property
  def organizations(self):
    return self.impl.organizations

  @property
  def tokens(self):
    return self.impl.tokens

  @property
  def training_runs(self):
    return self.impl.training_runs

  def pki_sessions(self):
    return self.impl.pki_sessions

def paginated_objects(api_object):
  def decorator(body, *args, **kwargs):
    return Pagination(api_object, body, *args, **kwargs)
  return decorator


# Allows response to be a single object of class some_class or a paginated
# response of objects that come from class some_class
def object_or_paginated_objects(api_object):
  def decorator(body, *args, **kwargs):
    if body.get('object') == 'pagination':
      return Pagination(api_object, body, *args, **kwargs)
    return api_object(body, *args, **kwargs)
  return decorator

_global_connection = None
def get_connection():
  global _global_connection
  if _global_connection is None:
    _global_connection = Connection(_show_deprecation_warning=False)
  return _global_connection
