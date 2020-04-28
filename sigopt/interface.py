import os

from .compat import json as simplejson
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
  Plan,
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
from .version import VERSION

class ConnectionImpl(object):
  def __init__(self, requestor, api_url=None):
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

    plan = ApiResource(
      self,
      'plan',
      endpoints=[
        ApiEndpoint(None, Plan, 'GET', 'fetch'),
      ],
    )

    best_assignments = ApiResource(
      self,
      'best_assignments',
      endpoints=[
        ApiEndpoint(None, object_or_paginated_objects(BestAssignments), 'GET', 'fetch'),
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

    training_runs = ApiResource(
      self,
      'training_runs',
      endpoints=[
        ApiEndpoint(None, TrainingRun, 'POST', 'create'),
        ApiEndpoint(None, object_or_paginated_objects(TrainingRun), 'GET', 'fetch')
      ],
      resources=[checkpoints]
    )

    experiment_tokens = ApiResource(
      self,
      'tokens',
      endpoints=[
        ApiEndpoint(None, Token, 'POST', 'create'),
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
        importances,
        metric_importances,
        observations,
        queued_suggestions,
        stopping_criteria,
        suggestions,
        experiment_tokens,
        training_runs,
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
      ],
    )

    client_tokens = ApiResource(
      self,
      'tokens',
      endpoints=[
        ApiEndpoint(None, object_or_paginated_objects(Token), 'GET', 'fetch'),
      ],
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
        client_tokens,
        plan,
      ],
    )

    self.organizations = ApiResource(
      self,
      'organizations',
      endpoints=[
        ApiEndpoint(None, object_or_paginated_objects(Organization), 'GET', 'fetch'),
      ],
    )

    self.pki_sessions = ApiResource(
      self,
      'pki_sessions',
      endpoints=[
        ApiEndpoint(None, Session, 'POST', 'create'),
      ],
    )

  def _request(self, method, url, params):
    if method.upper() in ('GET', 'DELETE'):
      json, params = None, self._request_params(params)
    else:
      json, params = ApiObject.as_json(params), None
    return self.requestor.request(
      method,
      url,
      json=json,
      params=params,
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
  def __init__(self, client_token=None, user_agent=None):
    client_token = client_token or os.environ.get('SIGOPT_API_TOKEN')
    api_url = os.environ.get('SIGOPT_API_URL') or DEFAULT_API_URL
    if not client_token:
      raise ValueError('Must provide client_token or set environment variable SIGOPT_API_TOKEN')

    default_headers = {
      'Content-Type': 'application/json',
      'User-Agent': user_agent if user_agent is not None else 'sigopt-python/{0}'.format(VERSION),
      'X-SigOpt-Python-Version': VERSION,
    }
    requestor = Requestor(
      client_token,
      '',
      default_headers,
    )
    self.impl = ConnectionImpl(requestor, api_url=api_url)

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
