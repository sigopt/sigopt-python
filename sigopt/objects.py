class ApiObject(object):
  def __init__(self, body):
    self.body = body

  def __repr__(self):
    return repr(self.body)

  def to_json(self):
    return self.body


class Assignments(ApiObject):
  def get(self, key):
    return self.body.get(key)

  def __getitem__(self, key):
    return self.body[key]


class Suggestion(ApiObject):
  @property
  def assignments(self):
    _assignments = self.body.get('assignments')
    return Assignments(_assignments) if _assignments is not None else None

  @property
  def expected_improvement(self):
    return self.body.get('expected_improvement')


class CategoricalValue(ApiObject):
  @property
  def name(self):
    return self.body.get('name')


class Bounds(ApiObject):
  @property
  def max(self):
    return self.body.get('max')

  @property
  def min(self):
    return self.body.get('min')


class ExperimentParameter(ApiObject):
  @property
  def name(self):
    return self.body.get('name')

  @property
  def type(self):
    return self.body.get('type')

  @property
  def bounds(self):
    _bounds = self.body.get('bounds')
    return Bounds(_bounds) if _bounds is not None else None

  @property
  def categorical_values(self):
    _categorical_values = self.body.get('categorical_values', [])
    return [CategoricalValue(cv) for cv in _categorical_values]

  @property
  def transformation(self):
    return self.body.get('transformation')


class ExperimentMetric(ApiObject):
  @property
  def name(self):
    return self.body.get('name')


class Client(ApiObject):
  @property
  def id(self):
    return self.body.get('id')

  @property
  def name(self):
    return self.body.get('name')


class Experiment(ApiObject):
  @property
  def id(self):
    return self.body.get('id')

  @property
  def name(self):
    return self.body.get('name')

  @property
  def parameters(self):
    _parameters = self.body.get('parameters', [])
    return [ExperimentParameter(p) for p in _parameters]

  @property
  def metric(self):
    _metric = self.body.get('metric')
    return ExperimentMetric(_metric) if _metric is not None else None
