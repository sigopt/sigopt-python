import copy
import six

from .compat import json


class ListOf(object):
  def __init__(self, type):
    self.type = type

  def __call__(self, value):
    return [self.type(v) for v in value]


Any = lambda x: x


class Field(object):
  def __init__(self, type):
    self.type = type

  def __call__(self, value):
    if value is None:
      return None
    return self.type(value)


class ApiObject(object):
  def __init__(self, body):
    self._body = body

  def __getattribute__(self, name):
    value = object.__getattribute__(self, name)
    if isinstance(value, Field):
      return value(self._body.get(name))
    return value

  def __repr__(self):
    return six.u('{0}({1})').format(
      self.__class__.__name__,
      json.dumps(self._body, sort_keys=True),
    )

  def to_json(self):
    return copy.deepcopy(self._body)

  def __eq__(self, other):
    return (
      isinstance(other, self.__class__) and
      self._body == other._body
    )


class Assignments(ApiObject):
  def get(self, key):
    return self._body.get(key)

  def __getitem__(self, key):
    return self._body[key]


class Bounds(ApiObject):
  max = Field(float)
  min = Field(float)


class CategoricalValue(ApiObject):
  enum_index = Field(int)
  name = Field(str)


class Client(ApiObject):
  created = Field(int)
  id = Field(str)
  name = Field(str)


class Metric(ApiObject):
  name = Field(str)


class Observation(ApiObject):
  assignments = Field(Assignments)
  created = Field(int)
  experiment = Field(str)
  failed = Field(bool)
  id = Field(str)
  metadata = Field(dict)
  suggestion = Field(str)
  value = Field(float)
  value_stddev = Field(float)


class Paging(ApiObject):
  after = Field(str)
  before = Field(str)


class Pagination(ApiObject):
  count = Field(int)
  paging = Field(Paging)

  def __init__(self, data_cls, body):
    super(Pagination, self).__init__(body)
    self.data_cls = data_cls

  @property
  def data(self):
    return Field(ListOf(self.data_cls))(self._body.get('data'))


class Parameter(ApiObject):
  bounds = Field(Bounds)
  categorical_values = Field(ListOf(CategoricalValue))
  default_value = Field(Any)
  name = Field(str)
  precision = Field(int)
  tunable = Field(bool)
  type = Field(str)


class PlanPeriod(ApiObject):
  end = Field(int)
  experiments = Field(ListOf(str))
  start = Field(int)


class PlanRules(ApiObject):
  max_dimension = Field(int)
  max_experiments = Field(int)
  max_observations = Field(int)
  max_parallelism = Field(int)


class Plan(ApiObject):
  current_period = Field(PlanPeriod)
  id = Field(str)
  name = Field(str)
  rules = Field(PlanRules)


class Progress(ApiObject):
  best_observation = Field(Observation)
  first_observation = Field(Observation)
  last_observation = Field(Observation)
  observation_count = Field(int)


class Suggestion(ApiObject):
  assignments = Field(Assignments)
  created = Field(int)
  experiment = Field(str)
  id = Field(str)
  metadata = Field(dict)
  state = Field(str)


class Experiment(ApiObject):
  can_be_deleted = Field(bool)
  client = Field(str)
  created = Field(int)
  id = Field(str)
  metadata = Field(dict)
  metric = Field(Metric)
  name = Field(str)
  parameters = Field(ListOf(Parameter))
  progress = Field(Progress)
  state = Field(str)
  type = Field(str)
