# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from .endpoint import ApiEndpoint
from .objects import (
  AIExperiment,
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
from .request_driver import RequestDriver
from .resource import ApiResource

class ConnectionImpl(object):
  def __init__(self, driver, user_agent=None):
    self.driver = driver

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

    aiexperiment_training_runs = ApiResource(
      self,
      'training_runs',
      endpoints=[
        ApiEndpoint(None, TrainingRun, 'POST', 'create'),
      ],
    )

    self.aiexperiments = ApiResource(
      self,
      'aiexperiments',
      endpoints=[
        ApiEndpoint(None, AIExperiment, 'POST', 'create'),
        ApiEndpoint(None, object_or_paginated_objects(AIExperiment), 'GET', 'fetch'),
        ApiEndpoint(None, AIExperiment, 'PUT', 'update'),
        ApiEndpoint(None, None, 'DELETE', 'delete'),
      ],
      resources=[
        aiexperiment_training_runs,
        best_training_runs,
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

    client_project_aiexperiments = ApiResource(
      self,
      'aiexperiments',
      endpoints=[
        ApiEndpoint(None, AIExperiment, 'POST', 'create'),
        ApiEndpoint(None, paginated_objects(AIExperiment), 'GET', 'fetch'),
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
        ApiEndpoint('batch', paginated_objects(TrainingRun), 'POST', 'create_batch'),
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
        client_project_aiexperiments,
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

    self.pki_sessions = ApiResource(
      self,
      'pki_sessions',
      endpoints=[
        ApiEndpoint(None, Session, 'POST', 'create'),
      ],
    )

  def _request(self, method, path, data, headers=None):
    return self.driver.request(
      method,
      path,
      data,
      headers,
    )

  def set_api_url(self, api_url):
    self.driver.set_api_url(api_url)

  def set_verify_ssl_certs(self, verify_ssl_certs):
    self.driver.verify_ssl_certs = verify_ssl_certs

  def set_proxies(self, proxies):
    self.driver.proxies = proxies

  def set_timeout(self, timeout):
    self.driver.timeout = timeout

  def set_client_ssl_certs(self, client_ssl_certs):
    self.driver.client_ssl_certs = client_ssl_certs

  def set_client_token(self, client_token):
    self.driver.set_client_token(client_token)

def instantiate_lite_driver(*args, **kwargs):
  try:
    from sigoptlite import LocalDriver  # pylint: disable=import-error
  except ModuleNotFoundError as mnfe:
    raise ModuleNotFoundError(
      "SigOpt Lite is not installed. It can be installed with the following command: `pip install 'sigopt[lite]'`"
    ) from mnfe
  return LocalDriver(*args, **kwargs)

DRIVER_KEY_HTTP = "http"
DRIVER_KEY_LITE = "lite"
driver_map = {
  DRIVER_KEY_HTTP: RequestDriver,
  DRIVER_KEY_LITE: instantiate_lite_driver,
}

def create_driver_instance(driver, args, kwargs):
  if isinstance(driver, str):
    try:
      driver = driver_map[driver]
    except KeyError as ke:
      raise ValueError(
        f"The driver {driver!r} is unknown."
        f" Only the following options are available: {list(driver_map.keys())}"
      ) from ke
  return driver(*args, **kwargs)


class Connection(object):
  """
  Client-facing interface for creating Connections.
  Shouldn't be changed without a major version change.
  """
  def __init__(self, *args, user_agent=None, driver="http", **kwargs):
    driver_instance = create_driver_instance(
      driver,
      args,
      kwargs,
    )
    self.impl = ConnectionImpl(driver=driver_instance, user_agent=user_agent)

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
  def aiexperiments(self):
    return self.impl.aiexperiments

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
    _global_connection = Connection()
  return _global_connection
