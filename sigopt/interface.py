import os

from .compat import json
from .endpoint import ApiEndpoint
from .objects import (
  ApiObject,
  BestAssignments,
  Client,
  Experiment,
  Observation,
  Pagination,
  Plan,
  Suggestion,
  StoppingCriteria,
  Token,
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
      ]
    )

    observations = ApiResource(
      self,
      'observations',
      endpoints=[
        ApiEndpoint(None, Observation, 'POST', 'create'),
        ApiEndpoint(None, object_or_paginated_objects(Observation), 'GET', 'fetch'),
        ApiEndpoint(None, Observation, 'PUT', 'update'),
        ApiEndpoint(None, None, 'DELETE', 'delete'),
      ]
    )

    plan = ApiResource(
      self,
      'plan',
      endpoints=[
        ApiEndpoint(None, Plan, 'GET', 'fetch'),
      ],
    )

    tokens = ApiResource(
      self,
      'tokens',
      endpoints=[
        ApiEndpoint(None, Token, 'POST', 'create'),
      ],
    )

    best_assignments = ApiResource(
      self,
      'best_assignments',
      endpoints=[
        ApiEndpoint(None, object_or_paginated_objects(BestAssignments), 'GET', 'fetch'),
      ],
    )

    stopping_criteria = ApiResource(
      self,
      'stopping_criteria',
      endpoints=[
        ApiEndpoint(None, StoppingCriteria, 'GET', 'fetch'),
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
        suggestions,
        observations,
        tokens,
        best_assignments,
        stopping_criteria,
      ]
    )

    client_experiments = ApiResource(
      self,
      'experiments',
      endpoints=[
        ApiEndpoint(None, Experiment, 'POST', 'create'),
        ApiEndpoint(None, lambda *args, **kwargs: Pagination(Experiment, *args, **kwargs), 'GET', 'fetch'),
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
        plan,
      ],
    )

  def _get(self, url, params=None):
    request_params = self._request_params(params)
    return self.requestor.get(
      url,
      params=request_params,
    )

  def _post(self, url, params=None):
    request_params = ApiObject.as_json(params)
    return self.requestor.post(
      url,
      json=request_params,
    )

  def _put(self, url, params=None):
    request_params = ApiObject.as_json(params)
    return self.requestor.put(
      url,
      json=request_params,
    )

  def _delete(self, url, params=None):
    request_params = ApiObject.as_json(params)
    return self.requestor.delete(
      url,
      params=request_params,
    )

  def _request_params(self, params):
    req_params = params or {}

    def serialize(value):
      if isinstance(value, (dict, list)):
        return json.dumps(value)
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

  @property
  def clients(self):
    return self.impl.clients

  @property
  def experiments(self):
    return self.impl.experiments


# Allows response to be a single object of class some_class or a paginated
# response of objects that come from class some_class
def object_or_paginated_objects(api_object):
  def decorator(body, *args, **kwargs):
    if body.get('object') == 'pagination':
      return Pagination(api_object, body, *args, **kwargs)
    return api_object(body, *args, **kwargs)
  return decorator
