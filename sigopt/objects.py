# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import copy
import warnings

from .compat import json
from .lib import is_integer, is_mapping, is_number, is_numpy_array, is_sequence, is_string


class ListOf(object):
  def __init__(self, typ):
    self.type = typ

  def __call__(self, value):
    return [self.type(v) for v in value]


class MapOf(object):
  def __init__(self, value_type, key_type=str):
    self.value_type = value_type
    self.key_type = key_type

  def __call__(self, value):
    d = {self.key_type(k): self.value_type(v) for k, v in value.items()}
    return d


def DictField(name, type_=str):
  return lambda value: type_(value[name])


Any = lambda x: x


class Field(object):
  def __init__(self, typ):
    self.type = typ

  def __call__(self, value):
    if value is None:
      return None
    return self.type(value)


class DeprecatedField(Field):
  def __init__(self, typ, recommendation=None):
    super().__init__(typ)
    self.recommendation = (" " + recommendation) if recommendation else ""

  def __call__(self, value):
    warnings.warn(
      "This field has been deprecated and may be removed in a future version.{0}".format(self.recommendation),
      DeprecationWarning,
    )
    return super().__call__(value)


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

  def _repr_keys(self):
    attributes = dir(self)
    attributes = [a for a in attributes if not a.startswith("_")]
    attributes = [a for a in attributes if not isinstance(getattr(self.__class__, a), DeprecatedField)]
    attributes = [a for a in attributes if not callable(getattr(self, a))]
    keys_in_json = set(ApiObject.as_json(self._body).keys())
    return keys_in_json.intersection(set(attributes))

  @staticmethod
  def _emit_repr(object_name, values_mapping):
    if values_mapping:
      return "{0}(\n{1}\n)".format(
        object_name,
        "\n".join(
          [
            "  {}={},".format(key, ApiObject.dumps(value, indent_level=2).lstrip())
            for key, value in values_mapping.items()
          ]
        ),
      )
    return "{0}()".format(object_name)

  def __repr__(self):
    keys = self._repr_keys()
    values = {key: getattr(self, key) for key in keys}
    return BaseApiObject._emit_repr(self.__class__.__name__, values)

  def to_json(self):
    return copy.deepcopy(self._body)


class ApiObject(BaseApiObject):
  def __init__(self, body, bound_endpoint=None, retrieve_params=None):
    super().__init__()
    object.__setattr__(self, "_body", body)
    object.__setattr__(self, "_bound_endpoint", bound_endpoint)
    object.__setattr__(self, "_retrieve_params", retrieve_params)

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self._body == other._body

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
    indent = " " * indent_level

    if isinstance(obj, BaseApiObject):
      return "{0}{1}".format(indent, str(obj).replace("\n", "\n{0}".format(indent)))
    if is_mapping(obj):
      if obj:
        return "{0}{{\n{1},\n{0}}}".format(
          indent,
          ",\n".join(
            [
              '  {0}"{1}"={2}'.format(
                indent,
                key,
                ApiObject.dumps(obj[key], indent_level=indent_level + 2).lstrip(),
              )
              for key in obj
            ]
          ),
        )
      return "{0}{1}".format(indent, str(obj))
    if is_numpy_array(obj):
      return ApiObject.dumps(obj.tolist(), indent_level=indent_level)
    if is_sequence(obj):
      if obj:
        return "{0}[\n{1},\n{0}]".format(
          indent,
          ",\n".join([ApiObject.dumps(c, indent_level=indent_level + 2) for c in obj]),
        )
      return "{0}{1}".format(indent, str(obj))
    if is_integer(obj):
      return "{0}{1}".format(indent, str(int(obj)))
    if is_number(obj):
      return "{0}{1}".format(indent, str(float(obj)))
    if is_string(obj):
      return '{0}"{1}"'.format(indent, obj)
    return "{0}{1}".format(indent, obj)


class _DictWrapper(BaseApiObject, dict):
  def __init__(self, body, bound_endpoint=None, retrieve_params=None):
    super().__init__()
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
    return isinstance(other, self.__class__) and dict.__eq__(self, other)

  def __repr__(self):
    return "{0}({1})".format(
      self.__class__.__name__,
      json.dumps(
        ApiObject.as_json(self._body),
        indent=2,
        sort_keys=True,
        separators=(",", ": "),
      ),
    )


class Assignments(_DictWrapper):
  pass


class Task(ApiObject):
  cost = Field(float)
  name = Field(str)


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
  organization = Field(str)


class Conditional(ApiObject):
  name = Field(str)
  values = Field(ListOf(str))


class Conditions(_DictWrapper):
  pass


class ImportancesMap(_DictWrapper):
  pass


class Importances(ApiObject):
  importances = Field(ImportancesMap)


class MetricImportances(ApiObject):
  importances = Field(ImportancesMap)
  metric = Field(str)


class Metadata(_DictWrapper):
  pass


class SysMetadata(_DictWrapper):
  pass


class MetricEvaluation(ApiObject):
  name = Field(str)
  value = Field(float)
  value_stddev = Field(float)


class Metric(ApiObject):
  name = Field(str)
  objective = Field(str)
  strategy = Field(str)
  threshold = Field(float)


class Observation(ApiObject):
  assignments = Field(Assignments)
  created = Field(int)
  experiment = Field(str)
  failed = Field(bool)
  id = Field(str)
  metadata = Field(Metadata)
  suggestion = Field(str)
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
  after = Field(str)
  before = Field(str)


class Pagination(ApiObject):
  count = Field(int)
  paging = Field(Paging)

  def __init__(self, data_cls, body, bound_endpoint=None, retrieve_params=None):
    super().__init__(body, bound_endpoint, retrieve_params)
    self.data_cls = data_cls

  def _repr_keys(self):
    return ["data", "count", "paging"]

  def __repr__(self):
    values = {
      "data": self._unsafe_data,
      "count": self.count,
      "paging": self.paging,
    }
    values = {k: v for k, v in values.items() if v is not None}
    return BaseApiObject._emit_repr("Pagination<{0}>".format(self.data_cls.__name__), values)

  @property
  def data(self):
    warnings.warn(
      (
        "The .data field only contains a single page of results, which may be"
        " incomplete for large responses. Prefer to use the `.iterate_pages()"
        " to ensure that you iterate through all elements in the response."
      ),
      RuntimeWarning,
    )
    return self._unsafe_data

  @property
  def _unsafe_data(self):
    return Field(ListOf(self.data_cls))(self._body.get("data"))

  def iterate_pages(self):
    # pylint: disable=no-member
    data = self._unsafe_data
    paging = self.paging or Paging({})

    use_before = "before" in self._retrieve_params or "after" not in self._retrieve_params

    while data:
      for d in data:
        yield d
      next_paging = dict(before=paging.before) if use_before else dict(after=paging.after)
      if next_paging.get("before") is not None or next_paging.get("after") is not None:
        params = self._retrieve_params.copy()
        if use_before:
          params["before"] = paging.before
          params.pop("after", None)
        else:
          params.pop("before", None)
          params["after"] = paging.after
        response = self._bound_endpoint(**params)
        data = response._unsafe_data
        paging = response.paging
      else:
        data = []
        paging = None
    # pylint: enable=no-member


class ParameterPrior(ApiObject):
  mean = Field(float)
  name = Field(str)
  scale = Field(float)
  shape_a = Field(float)
  shape_b = Field(float)


class Parameter(ApiObject):
  bounds = Field(Bounds)
  categorical_values = Field(ListOf(CategoricalValue))
  conditions = Field(Conditions)
  default_value = Field(Any)
  grid = Field(ListOf(float))
  name = Field(str)
  precision = Field(int)
  prior = Field(ParameterPrior)
  transformation = Field(str)
  tunable = DeprecatedField(bool)
  type = Field(str)


class Progress(ApiObject):
  # observation progress fields
  best_observation = DeprecatedField(Observation, recommendation="Prefer the `best_assignments` endpoint")
  first_observation = Field(Observation)
  last_observation = Field(Observation)
  observation_count = Field(int)
  observation_budget_consumed = Field(float)
  # run progress fields
  active_run_count = Field(int)
  finished_run_count = Field(int)
  total_run_count = Field(int)
  remaining_budget = Field(float)


class RunsProgress(ApiObject):
  active_run_count = Field(int)
  finished_run_count = Field(int)
  total_run_count = Field(int)
  remaining_budget = Field(float)


class Suggestion(ApiObject):
  assignments = Field(Assignments)
  created = Field(int)
  experiment = Field(str)
  id = Field(str)
  metadata = Field(Metadata)
  state = Field(str)
  task = Field(Task)


class QueuedSuggestion(ApiObject):
  assignments = Field(Assignments)
  created = Field(int)
  experiment = Field(str)
  id = Field(str)
  task = Field(Task)


class ConstraintTerm(ApiObject):
  name = Field(str)
  weight = Field(float)


class LinearConstraint(ApiObject):
  terms = Field(ListOf(ConstraintTerm))
  threshold = Field(float)
  type = Field(str)


class TrainingEarlyStoppingCriteria(ApiObject):
  lookback_checkpoints = Field(int)
  name = Field(str)
  metric = Field(str)
  min_checkpoints = Field(int)
  type = Field(str)


class TrainingMonitor(ApiObject):
  max_checkpoints = Field(int)
  early_stopping_criteria = Field(ListOf(TrainingEarlyStoppingCriteria))


class ExperimentTag(ApiObject):
  name = Field(str)
  created_by = Field(int)
  last_used = Field(int)


class Experiment(ApiObject):
  budget = Field(float)
  can_be_deleted = DeprecatedField(bool)
  client = Field(str)
  conditionals = Field(ListOf(Conditional))
  created = Field(int)
  development = Field(bool)
  id = Field(str)
  linear_constraints = Field(ListOf(LinearConstraint))
  metadata = Field(Metadata)
  metric = DeprecatedField(
    Metric,
    recommendation=(
      "Prefer the `metrics` field(see https://docs.sigopt.com/core-module-api-references/api-objects/object_experiment)"
    ),
  )
  metrics = Field(ListOf(Metric))
  name = Field(str)
  num_solutions = Field(int)
  observation_budget = Field(int)
  parameters = Field(ListOf(Parameter))
  parallel_bandwidth = Field(int)
  progress = Field(Progress)
  project = Field(str)
  state = Field(str)
  tags = Field(ListOf(str))
  tasks = Field(ListOf(Task))
  training_monitor = Field(TrainingMonitor)
  type = Field(str)
  updated = Field(int)
  user = Field(str)


class AIExperiment(ApiObject):
  budget = Field(float)
  client = Field(str)
  conditionals = Field(ListOf(Conditional))
  created = Field(int)
  id = Field(str)
  linear_constraints = Field(ListOf(LinearConstraint))
  metadata = Field(Metadata)
  metrics = Field(ListOf(Metric))
  name = Field(str)
  num_solutions = Field(int)
  parallel_bandwidth = Field(int)
  parameters = Field(ListOf(Parameter))
  progress = Field(RunsProgress)
  project = Field(str)
  state = Field(str)
  updated = Field(int)
  user = Field(str)


class Token(ApiObject):
  all_experiments = Field(bool)
  client = Field(str)
  development = Field(bool)
  experiment = Field(str)
  expires = Field(int)
  permissions = DeprecatedField(str)
  token = Field(str)
  token_type = Field(str)
  user = Field(str)


class BestAssignments(ApiObject):
  assignments = Field(Assignments)
  id = Field(str)
  value = Field(float)
  value_stddev = Field(float)
  values = Field(ListOf(MetricEvaluation))


class StoppingCriteria(ApiObject):
  should_stop = Field(bool)
  reasons = Field(ListOf(str))


class Project(ApiObject):
  id = Field(str)
  client = Field(str)
  name = Field(str)
  user = Field(str)
  created = Field(int)
  updated = Field(int)
  metadata = Field(Metadata)


class Model(ApiObject):
  type = Field(str)


class SourceCode(ApiObject):
  content = Field(str)
  hash = Field(str)


class TrainingRun(ApiObject):
  assignments = Field(Assignments)
  best_checkpoint = Field(str)
  client = Field(str)
  checkpoint_count = Field(int)
  completed = Field(int)
  created = Field(int)
  datasets = Field(ListOf(str))
  deleted = Field(bool)
  experiment = Field(str)
  files = Field(ListOf(str))
  finished = Field(bool)
  id = Field(str)
  logs = Field(MapOf(DictField("content")))
  metadata = Field(Metadata)
  model = Field(Model)
  name = Field(str)
  object = Field(str)
  observation = Field(str)
  project = Field(str)
  source_code = Field(SourceCode)
  state = Field(str)
  suggestion = Field(str)
  tags = Field(ListOf(str))
  updated = Field(int)
  user = Field(str)
  values = Field(MapOf(MetricEvaluation))
  sys_metadata = Field(SysMetadata)
  dev_metadata = Field(Metadata)


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
