import copy
import six

from .compat import json

class ApiObject(object):
  def __init__(self, body):
    self._body = body

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
  @property
  def max(self):
    return self._body.get('max')

  @property
  def min(self):
    return self._body.get('min')


class CategoricalValue(ApiObject):
  @property
  def name(self):
    return self._body.get('name')

  @property
  def enum_index(self):
    return self._body.get('enum_index')


class Client(ApiObject):
  @property
  def id(self):
    return self._body.get('id')

  @property
  def created(self):
    return self._body.get('created')

  @property
  def name(self):
    return self._body.get('name')


class Experiment(ApiObject):
  @property
  def id(self):
    return self._body.get('id')

  @property
  def created(self):
    return self._body.get('created')

  @property
  def name(self):
    return self._body.get('name')

  @property
  def type(self):
    return self._body.get('type')

  @property
  def state(self):
    return self._body.get('state')

  @property
  def can_be_deleted(self):
    return self._body.get('can_be_deleted')

  @property
  def parameters(self):
    _parameters = self._body.get('parameters', [])
    return [Parameter(p) for p in _parameters]

  @property
  def metric(self):
    _metric = self._body.get('metric')
    return Metric(_metric) if _metric is not None else None

  @property
  def progress(self):
    _progress = self._body.get('progress')
    return Progress(_progress) if _progress is not None else None

  @property
  def client(self):
    return self._body.get('client')


class Metric(ApiObject):
  @property
  def name(self):
    return self._body.get('name')


class Observation(ApiObject):
  @property
  def id(self):
    return self._body.get('id')

  @property
  def created(self):
      return self._body.get('created')

  @property
  def assignments(self):
    _assignments = self._body.get('assignments')
    return Assignments(_assignments) if _assignments is not None else None

  @property
  def value(self):
    return self._body.get('value')

  @property
  def value_stddev(self):
    return self._body.get('value_stddev')

  @property
  def failed(self):
    return self._body.get('failed')

  @property
  def suggestion(self):
    return self._body.get('suggestion')

  @property
  def experiment(self):
    return self._body.get('experiment')


class Paging(ApiObject):
  @property
  def before(self):
    return self._body.get('before')

  @property
  def after(self):
    return self._body.get('after')


class Pagination(ApiObject):
  def __init__(self, data_cls, body):
    super(Pagination, self).__init__(body)
    self.data_cls = data_cls

  @property
  def count(self):
    return self._body.get('count')

  @property
  def data(self):
    _data = self._body.get('data')
    return [self.data_cls(d) for d in _data]

  @property
  def paging(self):
    _paging = self._body.get('paging')
    return Paging(_paging) if _paging is not None else None


class Parameter(ApiObject):
  @property
  def name(self):
    return self._body.get('name')

  @property
  def type(self):
    return self._body.get('type')

  @property
  def tunable(self):
    return self._body.get('tunable')

  @property
  def bounds(self):
    _bounds = self._body.get('bounds')
    return Bounds(_bounds) if _bounds is not None else None

  @property
  def categorical_values(self):
    _categorical_values = self._body.get('categorical_values')
    if _categorical_values is not None:
      return [CategoricalValue(cv) for cv in _categorical_values]
    return None

  @property
  def precision(self):
    return self._body.get('precision')

  @property
  def default_value(self):
    return self._body.get('default_value')


class Progress(ApiObject):
  @property
  def observation_count(self):
    return self._body.get('observation_count')

  @property
  def best_observation(self):
    _observation = self._body.get('best_observation')
    return Observation(_observation) if _observation is not None else None

  @property
  def last_observation(self):
    _observation = self._body.get('last_observation')
    return Observation(_observation) if _observation is not None else None

  @property
  def first_observation(self):
    _observation = self._body.get('first_observation')
    return Observation(_observation) if _observation is not None else None


class Suggestion(ApiObject):
  @property
  def id(self):
    return self._body.get('id')

  @property
  def created(self):
    return self._body.get('created')

  @property
  def state(self):
    return self._body.get('state')

  @property
  def assignments(self):
    _assignments = self._body.get('assignments')
    return Assignments(_assignments) if _assignments is not None else None

  @property
  def experiment(self):
    return self._body.get('experiment')
