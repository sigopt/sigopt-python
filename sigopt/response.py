from .objects import ApiObject, Cohort, Client, Experiment, Observation, Role, Suggestion, User, Worker, Pagination

class ApiResponse(ApiObject):
  pass

class ExperimentsAllocateResponse(ApiResponse):
  @property
  def cohorts(self):
    _cohorts = self._body.get('cohorts')
    return [Cohort(c) for c in _cohorts]


class ExperimentsBestObservationResponse(ApiResponse):
  @property
  def observation(self):
    _observation = self._body.get('observation')
    return Observation(_observation) if _observation else None


class ExperimentsCreateResponse(ApiResponse):
  @property
  def experiment(self):
    _experiment = self._body.get('experiment')
    return Experiment(_experiment) if _experiment is not None else None


class ExperimentsCreateCohortResponse(ApiResponse):
  @property
  def cohort(self):
    _cohort = self._body.get('cohort')
    return Cohort(_cohort) if _cohort is not None else None


class ExperimentsHistoryResponse(ApiResponse):
  @property
  def observations(self):
    _observations = self._body.get('observations')
    return Pagination(Observation, _observations)


class ExperimentsUpdateCohortResponse(ApiResponse):
  @property
  def cohort(self):
    _cohort = self._body.get('cohort')
    return Cohort(_cohort) if _cohort is not None else None


class ExperimentResponse(ApiResponse):
  @property
  def experiment(self):
    _experiment = self._body.get('experiment')
    return Experiment(_experiment) if _experiment is not None else None


class ExperimentsSuggestResponse(ApiResponse):
  @property
  def suggestion(self):
    _suggestion = self._body.get('suggestion')
    return Suggestion(_suggestion) if _suggestion is not None else None


class ExperimentsSuggestMultiResponse(ApiResponse):
  @property
  def suggestions(self):
    _suggestions = self._body.get('suggestions')
    return [Suggestion(s) for s in _suggestions]


class ExperimentsWorkersResponse(ApiResponse):
  @property
  def workers(self):
    _workers = self._body.get('workers')
    return [Worker(w) for w in _workers]


class ClientResponse(ApiResponse):
  @property
  def client(self):
    _client = self._body.get('client')
    return Client(_client) if _client is not None else None

  @property
  def client_token(self):
    return self._body.get('client_token')


class ClientsExperimentsResponse(ApiResponse):
  @property
  def experiments(self):
    _experiments = self._body.get('experiments', [])
    return [Experiment(e) for e in _experiments]


class UserResponse(ApiResponse):
  @property
  def user(self):
    _user = self._body.get('user')
    return User(_user) if _user is not None else None


class UsersRolesResponse(ApiResponse):
  @property
  def roles(self):
    _roles = self._body.get('roles', [])
    return [Role(r) for r in _roles]

# Allows response to be a single object of class some_class or a paginated
# response of objects that come from class some_class
def object_or_paginated_objects(api_object):
  def decorator(body):
    if body.get('object') == 'pagination':
      return Pagination(api_object, body)
    else:
      return api_object(body)

  return decorator

def paginated_objects(api_object):
  def decorator(body):
    if isinstance(body, list):
      return [api_object(obj) for obj in body]
    else:
      return Pagination(api_object, body)
  return decorator
