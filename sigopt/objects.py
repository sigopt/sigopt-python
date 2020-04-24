import copy
import warnings

from .compat import json
from .lib import is_sequence, is_mapping, is_integer, is_number, is_numpy_array, is_string
from .vendored import six as six


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
    attributes = dir(self)
    attributes = [a for a in attributes if not a.startswith('_')]
    attributes = [a for a in attributes if not callable(getattr(self, a))]
    keys_in_json = set(ApiObject.as_json(self._body).keys())
    keys = keys_in_json.intersection(set(attributes))

    if keys:
      return six.u('{0}(\n{1}\n)').format(
        self.__class__.__name__,
        '\n'.join([
          six.u('  {}={},').format(key, ApiObject.dumps(getattr(self, key), indent_level=2).lstrip())
          for key
          in keys
        ]),
      )
    return six.u('{0}()').format(self.__class__.__name__)

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
    if is_mapping(obj):
      c = {}
      for key in obj:
        c[key] = ApiObject.as_json(obj[key])
      return c
    if is_numpy_array(obj):
      return ApiObject.as_json(obj.tolist())
    if is_sequence(obj):
      return [ApiObject.as_json(c) for c in obj]
    if is_integer(obj):
      return int(obj)
    if is_number(obj):
      return float(obj)
    return obj

  @staticmethod
  def dumps(obj, indent_level=0):
    indent = ' ' * indent_level

    if isinstance(obj, BaseApiObject):
      return six.u('{0}{1}'.format(indent, str(obj).replace('\n', '\n{0}'.format(indent))))
    if is_mapping(obj):
      if obj:
        return six.u('{0}{\n{1},\n{0}}').format(
          indent,
          six.u(',\n').join([
            six.u('  {0}"{1}"={2}').format(
              indent,
              key,
              ApiObject.dumps(obj[key], indent_level=indent_level + 2).lstrip()
            )
            for key
            in obj
          ])
        )
      return six.u('{0}{1}'.format(indent, str(obj)))
    if is_numpy_array(obj):
      return ApiObject.dumps(obj.tolist(), indent_level=indent_level)
    if is_sequence(obj):
      if obj:
        return six.u('{0}[\n{1},\n{0}]').format(
          indent,
          six.u(',\n').join([
            ApiObject.dumps(c, indent_level=indent_level + 2)
            for c
            in obj
          ])
        )
      return six.u('{0}{1}'.format(indent, str(obj)))
    if is_integer(obj):
      return six.u('{0}{1}'.format(indent, str(int(obj))))
    if is_number(obj):
      return six.u('{0}{1}'.format(indent, str(float(obj))))
    if is_string(obj):
      return six.u('{0}"{1}"'.format(indent, obj))
    return six.u('{0}{1}'.format(indent, obj))

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

  def __repr__(self):
    return six.u('{0}({1})').format(
      self.__class__.__name__,
      json.dumps(
        ApiObject.as_json(self._body),
        indent=2,
        sort_keys=True,
        separators=(',', ': '),
      ),
    )

class Assignments(_DictWrapper):
  pass


class Task(ApiObject):
  cost = Field(float)
  name = Field(six.text_type)


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


class Conditional(ApiObject):
  name = Field(six.text_type)
  values = Field(ListOf(six.text_type))


class Conditions(_DictWrapper):
  pass


class ImportancesMap(_DictWrapper):
  pass


class Importances(ApiObject):
  importances = Field(ImportancesMap)


class MetricImportances(ApiObject):
  importances = Field(ImportancesMap)
  metric = Field(six.text_type)


class Metadata(_DictWrapper):
  pass


class MetricEvaluation(ApiObject):
  name = Field(six.text_type)
  value = Field(float)
  value_stddev = Field(float)


class Metric(ApiObject):
  name = Field(six.text_type)
  objective = Field(six.text_type)
  strategy = Field(six.text_type)
  threshold = Field(float)


class Observation(ApiObject):
  assignments = Field(Assignments)
  created = Field(int)
  experiment = Field(six.text_type)
  failed = Field(bool)
  id = Field(six.text_type)
  metadata = Field(Metadata)
  suggestion = Field(six.text_type)
  task = Field(Task)
  value = Field(float)
  value_stddev = Field(float)
  values = Field(ListOf(MetricEvaluation))


class Organization(ApiObject):
  created = Field(int)
  deleted = Field(bool)
  id = Field(str)
  name = Field(str)


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
    # pylint: disable=no-member
    data = self.data
    paging = self.paging or Paging({})

    use_before = 'before' in self._retrieve_params or 'after' not in self._retrieve_params

    while data:
      for d in data:
        yield d
      next_paging = dict(before=paging.before) if use_before else dict(after=paging.after)
      if next_paging.get('before') is not None or next_paging.get('after') is not None:
        params = self._retrieve_params.copy()
        if use_before:
          params['before'] = paging.before
          params.pop('after', None)
        else:
          params.pop('before', None)
          params['after'] = paging.after
        response = self._bound_endpoint(**params)
        data = response.data
        paging = response.paging
      else:
        data = []
        paging = None
    # pylint: enable=no-member


class Parameter(ApiObject):
  bounds = Field(Bounds)
  categorical_values = Field(ListOf(CategoricalValue))
  conditions = Field(Conditions)
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
  max_clients = Field(int)
  max_conditionals_breadth = Field(int)
  max_constraints = Field(int)
  max_dimension = Field(int)
  max_experiments = Field(int)
  max_metrics = Field(int)
  max_observations = Field(int)
  max_parallelism = Field(int)
  max_solutions = Field(int)
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
  observation_budget_consumed = Field(float)


class Suggestion(ApiObject):
  assignments = Field(Assignments)
  created = Field(int)
  experiment = Field(six.text_type)
  id = Field(six.text_type)
  metadata = Field(Metadata)
  state = Field(six.text_type)
  task = Field(Task)


class QueuedSuggestion(ApiObject):
  assignments = Field(Assignments)
  created = Field(int)
  experiment = Field(str)
  id = Field(str)
  task = Field(Task)


class ConstraintTerm(ApiObject):
  name = Field(six.text_type)
  weight = Field(float)


class LinearConstraint(ApiObject):
  terms = Field(ListOf(ConstraintTerm))
  threshold = Field(float)
  type = Field(six.text_type)


class TrainingEarlyStoppingCriteria(ApiObject):
  lookback_checkpoints = Field(int)
  name = Field(six.text_type)
  metric = Field(six.text_type)
  min_checkpoints = Field(int)
  type = Field(six.text_type)


class TrainingMonitor(ApiObject):
  max_checkpoints = Field(int)
  early_stopping_criteria = Field(ListOf(TrainingEarlyStoppingCriteria))

class Experiment(ApiObject):
  can_be_deleted = DeprecatedField(bool)
  client = Field(six.text_type)
  conditionals = Field(ListOf(Conditional))
  created = Field(int)
  development = Field(bool)
  id = Field(six.text_type)
  linear_constraints = Field(ListOf(LinearConstraint))
  metadata = Field(Metadata)
  metric = DeprecatedField(
    Metric,
    recommendation='Prefer the `metrics` field (see https://sigopt.com/docs/objects/experiment)'
  )
  metrics = Field(ListOf(Metric))
  name = Field(six.text_type)
  num_solutions = Field(int)
  observation_budget = Field(int)
  parameters = Field(ListOf(Parameter))
  parallel_bandwidth = Field(int)
  progress = Field(Progress)
  project = Field(six.text_type)
  state = Field(six.text_type)
  tasks = Field(ListOf(Task))
  training_monitor = Field(TrainingMonitor)
  type = Field(six.text_type)
  updated = Field(int)
  user = Field(six.text_type)


class Token(ApiObject):
  all_experiments = Field(bool)
  client = Field(six.text_type)
  development = Field(bool)
  experiment = Field(six.text_type)
  expires = Field(int)
  permissions = DeprecatedField(six.text_type)
  token = Field(six.text_type)
  token_type = Field(six.text_type)
  user = Field(six.text_type)


class BestAssignments(ApiObject):
  assignments = Field(Assignments)
  id = Field(str)
  value = Field(float)
  value_stddev = Field(float)
  values = Field(ListOf(MetricEvaluation))


class StoppingCriteria(ApiObject):
  should_stop = Field(bool)
  reasons = Field(ListOf(six.text_type))


class Project(ApiObject):
  id = Field(six.text_type)
  client = Field(six.text_type)
  name = Field(six.text_type)
  user = Field(six.text_type)
  created = Field(int)
  updated = Field(int)
  metadata = Field(Metadata)


class TrainingRun(ApiObject):
  id = Field(str)
  best_checkpoint = Field(str)
  checkpoint_count = Field(int)
  created = Field(int)
  finished = Field(bool)
  metadata = Field(Metadata)
  observation = Field(str)
  suggestion = Field(str)
  updated = Field(int)


class StoppingReasons(_DictWrapper):
  pass


class Checkpoint(ApiObject):
  id = Field(str)
  created = Field(int)
  metadata = Field(Metadata)
  should_stop = Field(bool)
  stopping_reasons = Field(StoppingReasons)
  training_run = Field(str)
  values = Field(ListOf(MetricEvaluation))


class User(ApiObject):
  created = Field(int)
  deleted = Field(bool)
  email = Field(str)
  id = Field(str)
  name = Field(str)


class Session(ApiObject):
  api_token = Field(Token)
  client = Field(Client)
  user = Field(User)
