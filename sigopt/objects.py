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
  def __init__(self, type, recommendation=None):
    super(DeprecatedField, self).__init__(type)
    self.recommendation = (' ' + recommendation) if recommendation else ''

  def __call__(self, value):
    warnings.warn(
      'This field has been deprecated and may be removed in a future version.{0}'.format(self.recommendation),
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
      json.dumps(
        ApiObject.as_json(self._body),
        indent=2,
        sort_keys=True,
        separators=(',',': '),
      ),
    )

  def to_json(self):
    return copy.deepcopy(self._body)


class ApiObject(BaseApiObject):
  def __init__(self, body, bound_endpoint=None, retrieve_params=None):
    super(ApiObject, self).__init__()
    object.__setattr__(self, '_body', body)
    object.__setattr__(self, '_bound_endpoint', bound_endpoint)
    object.__setattr__(self, '_retrieve_params', retrieve_params)

  def __eq__(self, other):
    return (
      isinstance(other, self.__class__) and
      self._body == other._body
    )

  @staticmethod
  def as_json(obj):
    if isinstance(obj, BaseApiObject):
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
  def __init__(self, body, bound_endpoint=None, retrieve_params=None):
    super(_DictWrapper, self).__init__()
    dict.__init__(self, body)
    self._bound_endpoint = bound_endpoint
    self._retrieve_params = retrieve_params

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
  id = Field(six.text_type)
  name = Field(six.text_type)


class Metadata(_DictWrapper):
  pass


class MetricEvaluation(ApiObject):
  name = Field(six.text_type)
  value = Field(float)
  value_stddev = Field(float)


class Metric(ApiObject):
  name = Field(six.text_type)


class Observation(ApiObject):
  assignments = Field(Assignments)
  created = Field(int)
  experiment = Field(six.text_type)
  failed = Field(bool)
  id = Field(six.text_type)
  metadata = Field(Metadata)
  suggestion = Field(six.text_type)
  value = Field(float)
  value_stddev = Field(float)
  values = Field(ListOf(MetricEvaluation))


class Paging(ApiObject):
  after = Field(six.text_type)
  before = Field(six.text_type)


class Pagination(ApiObject):
  count = Field(int)
  paging = Field(Paging)

  def __init__(self, data_cls, body, bound_endpoint=None, retrieve_params=None):
    super(Pagination, self).__init__(body, bound_endpoint, retrieve_params)
    self.data_cls = data_cls

  @property
  def data(self):
    return Field(ListOf(self.data_cls))(self._body.get('data'))

  def iterate_pages(self):
    data = self.data
    paging = self.paging or Paging({})
    use_before = bool(paging.before)
    while data:
      for d in data:
        yield d
      next_paging = dict(before=paging.before) if use_before else dict(after=paging.after)
      if next_paging.get('before') is not None or next_paging.get('after') is not None:
        params = self._retrieve_params.copy()
        params.pop('before', None)
        params.pop('after', None)
        params.update(next_paging)
        response = self._bound_endpoint(**params)
        data = response.data
        paging = response.paging
      else:
        data = []
        paging = None


class Parameter(ApiObject):
  bounds = Field(Bounds)
  categorical_values = Field(ListOf(CategoricalValue))
  default_value = Field(Any)
  name = Field(six.text_type)
  precision = Field(int)
  tunable = DeprecatedField(bool)
  type = Field(six.text_type)


class PlanPeriod(ApiObject):
  end = Field(int)
  experiments = Field(ListOf(six.text_type))
  start = Field(int)


class PlanRules(ApiObject):
  max_categorical_breadth = Field(int)
  max_dimension = Field(int)
  max_experiments = Field(int)
  max_observations = Field(int)
  max_parallelism = Field(int)
  max_users = Field(int)


class Plan(ApiObject):
  current_period = Field(PlanPeriod)
  id = Field(six.text_type)
  name = Field(six.text_type)
  rules = Field(PlanRules)


class Progress(ApiObject):
  best_observation = DeprecatedField(Observation, recommendation='Prefer the `best_assignments` endpoint')
  first_observation = Field(Observation)
  last_observation = Field(Observation)
  observation_count = Field(int)


class Suggestion(ApiObject):
  assignments = Field(Assignments)
  created = Field(int)
  experiment = Field(six.text_type)
  fold = Field(six.text_type)
  fold_index = Field(int)
  id = Field(six.text_type)
  metadata = Field(Metadata)
  state = Field(six.text_type)


class Experiment(ApiObject):
  can_be_deleted = DeprecatedField(bool)
  client = Field(six.text_type)
  created = Field(int)
  development = Field(bool)
  folds = Field(int)
  id = Field(six.text_type)
  metadata = Field(Metadata)
  metric = Field(Metric)
  metrics = Field(ListOf(Metric))
  name = Field(six.text_type)
  observation_budget = Field(int)
  parameters = Field(ListOf(Parameter))
  progress = Field(Progress)
  state = Field(six.text_type)
  type = Field(six.text_type)


class Token(ApiObject):
  all_experiments = Field(bool)
  development = Field(bool)
  permissions = Field(six.text_type)
  token = Field(six.text_type)
  client = Field(six.text_type)
  experiment = Field(six.text_type)
  user = Field(six.text_type)


class BestAssignments(ApiObject):
  assignments = Field(Assignments)
  value = Field(float)
  value_stddev = Field(float)
  values = Field(ListOf(MetricEvaluation))
