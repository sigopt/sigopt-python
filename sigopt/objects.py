import copy
import warnings

from .compat import json
import sigopt.vendored.six as six


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


class DeprecatedField(Field):
  def __call__(self, value):
    warnings.warn(
      'This field has been deprecated and may be removed in a future version.',
      DeprecationWarning,
    )
    return super(DeprecatedField, self).__call__(value)


class BaseApiObject(object):
  def __getattribute__(self, name):
    value = object.__getattribute__(self, name)
    if isinstance(value, Field):
      return value(self._body.get(name))
    return value

  def __setattr__(self, name, value):
    field = self._get_field(name)
    if field:
      value = ApiObject.as_json(value)
      self._body[name] = value
    else:
      object.__setattr__(self, name, value)

  def __delattr__(self, name):
    field = self._get_field(name)
    if field:
      del self._body[name]
    else:
      object.__delattr__(self, name)

  def _get_field(self, name):
    try:
      subvalue = object.__getattribute__(self, name)
    except AttributeError:
      return None
    else:
      return subvalue if isinstance(subvalue, Field) else None

  def __repr__(self):
    return six.u('{0}({1})').format(
      self.__class__.__name__,
      json.dumps(ApiObject.as_json(self._body)),
    )

  def to_json(self):
    return copy.deepcopy(self._body)


class ApiObject(BaseApiObject):
  def __init__(self, body):
    super(ApiObject, self).__init__()
    object.__setattr__(self, '_body', body)

  def __eq__(self, other):
    return (
      isinstance(other, self.__class__) and
      self._body == other._body
    )

  @staticmethod
  def as_json(obj):
    if isinstance(obj, ApiObject):
      return obj.to_json()
    elif isinstance(obj, dict):
      c = {}
      for key in obj:
        c[key] = ApiObject.as_json(obj[key])
      return c
    elif isinstance(obj, list):
      return [ApiObject.as_json(c) for c in obj]
    else:
      return obj


class _DictWrapper(BaseApiObject, dict):
  def __init__(self, body):
    super(_DictWrapper, self).__init__()
    dict.__init__(self, body)

  @property
  def _body(self):
    return self

  def to_json(self):
    return dict(copy.deepcopy(self))

  def copy(self):
    return self.__class__(dict.copy(self))

  def __eq__(self, other):
    return (
      isinstance(other, self.__class__) and
      dict.__eq__(self, other)
    )


class Assignments(_DictWrapper):
  pass


class Bounds(ApiObject):
  max = Field(float)
  min = Field(float)


class CategoricalValue(ApiObject):
  enum_index = Field(int)
  name = Field(six.text_type)


class Client(ApiObject):
  created = Field(int)
  id = Field(str)
  name = Field(six.text_type)


class Metadata(_DictWrapper):
  pass


class Metric(ApiObject):
  name = Field(six.text_type)


class Observation(ApiObject):
  assignments = Field(Assignments)
  created = Field(int)
  experiment = Field(str)
  failed = Field(bool)
  id = Field(str)
  metadata = Field(Metadata)
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
  name = Field(six.text_type)
  precision = Field(int)
  tunable = DeprecatedField(bool)
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
  metadata = Field(Metadata)
  state = Field(str)


class Experiment(ApiObject):
  can_be_deleted = DeprecatedField(bool)
  client = Field(str)
  created = Field(int)
  id = Field(str)
  metadata = Field(Metadata)
  metric = Field(Metric)
  name = Field(six.text_type)
  parameters = Field(ListOf(Parameter))
  progress = Field(Progress)
  state = Field(str)
  type = Field(str)
