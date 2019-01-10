import os
import math
import numpy
import pytest
import warnings

from sigopt.objects import *

warnings.simplefilter("always")

def load(filename):
  with open(os.path.join(os.path.dirname(__file__), 'json', filename), 'r') as f:
    return json.load(f)

def load_and_parse(Cls, filename):
  json = load(filename)
  obj = Cls(json)
  assert obj.to_json() == json
  assert ApiObject.as_json(obj) == json
  return obj

class TestBase(object):
  def test_as_json(self):
    assert ApiObject.as_json(None) is None
    assert ApiObject.as_json(False) is False
    assert ApiObject.as_json(True) is True
    assert ApiObject.as_json(1) == 1
    assert ApiObject.as_json(1.1) == 1.1
    assert ApiObject.as_json(numpy.int8(4)) == 4
    assert ApiObject.as_json(numpy.int32(4)) == 4
    assert ApiObject.as_json(numpy.int64(4)) == 4
    assert ApiObject.as_json(numpy.float16(5.5)) == 5.5
    assert ApiObject.as_json(numpy.float32(5.5)) == 5.5
    assert ApiObject.as_json(numpy.float64(5.5)) == 5.5
    assert ApiObject.as_json('abc') == 'abc'

    assert ApiObject.as_json({}) == {}
    assert ApiObject.as_json({"a": "b"}) == {"a": "b"}
    assert ApiObject.as_json(Assignments({"a": "b"})) == {"a": "b"}
    assert ApiObject.as_json(Experiment({"name": "test"})) == {"name": "test"}
    assert ApiObject.as_json(Experiment({"bounds": {"min": 0}})) == {"bounds": {"min": 0}}

    assert ApiObject.as_json([]) == []
    assert ApiObject.as_json([1, 2, 3]) == [1, 2, 3]
    assert ApiObject.as_json([[1], 2, 3]) == [[1], 2, 3]
    assert ApiObject.as_json((1, 2, 3)) == [1, 2, 3]
    assert ApiObject.as_json(numpy.array([1, 2, 3], dtype=numpy.int64)) == [1, 2, 3]
    assert ApiObject.as_json(numpy.array([Experiment({})])) == [{}]
    assert ApiObject.as_json(["abc"]) == ["abc"]
    assert ApiObject.as_json([Assignments({"a": "b"})]) == [{"a": "b"}]
    assert ApiObject.as_json([Experiment({"name": "test"})]) == [{"name": "test"}]

  def test_equality(self):
    assert Experiment({}) == Experiment({})
    assert Experiment({}) != {}
    assert {} != Experiment({})
    assert Bounds({}) != Experiment({})

    assert Experiment({'a': 'b'}) == Experiment({'a': 'b'})
    assert Experiment({'a': 'b'}) != Experiment({})
    assert Experiment({'a': 'b'}) != Experiment({'a': 'c'})
    assert Experiment({'a': 'b'}) != Experiment({'a': 'b', 'c': 'd'})

    assert Assignments({'a': 'b'}) == Assignments({'a': 'b'})
    assert Assignments({'a': 'b'}) != Assignments({})
    assert Assignments({'a': 'b'}) != Assignments({'a': 'c'})
    assert Assignments({'a': 'b'}) != Assignments({'a': 'b', 'c': 'd'})

  def test_repr(self):
    assert repr(Experiment({})) == 'Experiment()'
    assert repr(Experiment({'user': 'b'})) == 'Experiment(\n  user="b",\n)'
    assert repr(Assignments({})) == 'Assignments({})'
    assert repr(Assignments({'a': 'b'})) == 'Assignments({\n  "a": "b"\n})'
    assert repr(Assignments({'a': 'b', 'c': 'd'})) == 'Assignments({\n  "a": "b",\n  "c": "d"\n})'
    assert (
        repr(Bounds({'max': 0.1, 'min': -0.2})) == 'Bounds(\n  max=0.1,\n  min=-0.2,\n)'
        or repr(Bounds({'max': 0.1, 'min': -0.2})) == 'Bounds(\n  min=-0.2,\n  max=0.1,\n)'
    )

  def test_json(self):
    assert Experiment({}).to_json() == {}
    assert Experiment({'bounds': {'min': 1, 'max': 2}}).to_json() == {'bounds': {'min': 1, 'max': 2}}
    assert Assignments({}).to_json() == {}
    assert Assignments({'abc': 'def', 'ghi': 123}).to_json() == {'abc': 'def', 'ghi': 123}

  def test_dict_like(self):
    a = Assignments({'abc': 'def', 'ghi': 123})
    assert a['abc'] == 'def'
    assert a.get('abc') == 'def'
    assert a.get('abc', 'fake') == 'def'
    assert a['ghi'] == 123
    assert a.get('ghi') == 123
    assert a.get('ghi', 'fake') == 123

    with pytest.raises(AttributeError):
      a.method_that_doesnt_exist_on_dict()

    with pytest.raises(KeyError):
      a['xyz']
    assert a.get('xyz') is None
    assert a.get('xyz', 'fake') == 'fake'

    assert len(a) == 2
    assert set(a.keys()) == set(('abc', 'ghi'))
    assert 'abc' in a
    assert 'xyz' not in a

    a['abc'] = 123
    a['lmn'] = 'pqr'
    assert a['abc'] == 123
    assert a['lmn'] == 'pqr'
    assert a.to_json()['abc'] == 123
    assert a.to_json()['lmn'] == 'pqr'

    assert a.copy() == a


class TestObjects(object):
  @pytest.fixture
  def experiment(self):
    return load_and_parse(Experiment, 'experiment.json')

  def test_experiment(self, experiment):
    assert experiment.id == '123'
    assert experiment.name == 'Test Experiment'
    assert experiment.type == 'cross_validated'
    assert experiment.created == 321
    assert isinstance(experiment.metrics[0], Metric)
    assert experiment.metrics[0].name == 'Revenue'
    assert isinstance(experiment.metrics[1], Metric)
    assert experiment.metrics[1].name == 'Sales'
    assert experiment.client == '678'
    assert experiment.linear_constraints
    assert experiment.linear_constraints[0]
    assert experiment.linear_constraints[0].type == 'greater_than'
    assert experiment.linear_constraints[0].threshold == 5
    assert experiment.linear_constraints[0].terms
    assert experiment.linear_constraints[0].terms[0].name == 'a'
    assert experiment.linear_constraints[0].terms[0].weight == 2
    assert experiment.conditionals
    assert experiment.conditionals[0]
    assert experiment.conditionals[0].name == 'num_hidden_layers'
    assert experiment.conditionals[0].values == ['1', '3']
    assert isinstance(experiment.progress, Progress)
    assert experiment.progress.observation_count == 3
    assert experiment.progress.observation_budget_consumed == 3.0
    assert isinstance(experiment.progress.first_observation, Observation)
    assert experiment.progress.first_observation.id == '1'
    assert isinstance(experiment.progress.first_observation.assignments, Assignments)
    assert experiment.progress.first_observation.assignments.get('a') == 1
    assert experiment.progress.first_observation.assignments.get('b') == 'c'
    assert experiment.progress.first_observation.values[0].name == 'Revenue'
    assert experiment.progress.first_observation.values[0].value == 3.1
    assert experiment.progress.first_observation.values[0].value_stddev is None
    assert experiment.progress.first_observation.values[1].name == 'Sales'
    assert experiment.progress.first_observation.values[1].value == 2.5
    assert experiment.progress.first_observation.values[1].value_stddev is None
    assert experiment.progress.first_observation.failed is False
    assert experiment.progress.first_observation.created == 451
    assert experiment.progress.first_observation.suggestion == '11'
    assert experiment.progress.first_observation.experiment == '123'
    assert isinstance(experiment.progress.last_observation, Observation)
    assert experiment.progress.last_observation.id == '2'
    assert isinstance(experiment.progress.last_observation.assignments, Assignments)
    assert experiment.progress.last_observation.assignments.get('a') == 2
    assert experiment.progress.last_observation.assignments.get('b') == 'd'
    assert experiment.progress.last_observation.values[0].name == 'Revenue'
    assert experiment.progress.last_observation.values[0].value == 3.1
    assert experiment.progress.last_observation.values[0].value_stddev == 0.5
    assert experiment.progress.last_observation.values[1].name == 'Sales'
    assert experiment.progress.last_observation.values[1].value == 2.5
    assert experiment.progress.last_observation.values[1].value_stddev == 0.8
    assert experiment.progress.last_observation.failed is False
    assert experiment.progress.last_observation.created == 452
    assert experiment.progress.last_observation.suggestion == '12'
    assert experiment.progress.last_observation.experiment == '123'
    assert isinstance(experiment.progress.best_observation, Observation)
    assert experiment.progress.best_observation.id == '3'
    assert isinstance(experiment.progress.best_observation.assignments, Assignments)
    assert experiment.progress.best_observation.assignments.get('a') == 3
    assert experiment.progress.best_observation.assignments.get('b') == 'd'
    assert experiment.progress.best_observation.values[0].name == 'Revenue'
    assert experiment.progress.best_observation.values[0].value is None
    assert experiment.progress.best_observation.values[0].value_stddev is None
    assert experiment.progress.best_observation.values[1].name == 'Sales'
    assert experiment.progress.best_observation.values[1].value is None
    assert experiment.progress.best_observation.values[1].value_stddev is None
    assert experiment.progress.best_observation.failed is True
    assert experiment.progress.best_observation.created == 453
    assert experiment.progress.best_observation.suggestion == '13'
    assert experiment.progress.best_observation.experiment == '123'
    assert isinstance(experiment.progress.best_observation.metadata, Metadata)
    assert experiment.progress.best_observation.metadata['abc'] == 'def'
    assert experiment.progress.best_observation.metadata['ghi'] == 123
    assert len(experiment.parameters) == 2
    assert isinstance(experiment.parameters[0], Parameter)
    assert experiment.parameters[0].name == 'a'
    assert experiment.parameters[0].type == 'double'
    assert isinstance(experiment.parameters[0].bounds, Bounds)
    assert experiment.parameters[0].bounds.min == 1
    assert experiment.parameters[0].bounds.max == 2
    assert experiment.parameters[0].categorical_values is None
    assert experiment.parameters[0].precision == 3
    assert experiment.parameters[0].default_value == 2
    assert isinstance(experiment.parameters[0].conditions, Conditions)
    assert experiment.parameters[0].conditions['num_hidden_layers'] == []
    assert isinstance(experiment.parameters[1], Parameter)
    assert experiment.parameters[1].name == 'b'
    assert experiment.parameters[1].type == 'categorical'
    assert experiment.parameters[1].bounds is None
    assert len(experiment.parameters[1].categorical_values) == 2
    assert isinstance(experiment.parameters[1].categorical_values[0], CategoricalValue)
    assert experiment.parameters[1].categorical_values[0].name == 'c'
    assert experiment.parameters[1].categorical_values[0].enum_index == 1
    assert experiment.parameters[1].categorical_values[1].name == 'd'
    assert experiment.parameters[1].categorical_values[1].enum_index == 2
    assert experiment.parameters[1].precision is None
    assert experiment.parameters[1].default_value is None
    assert isinstance(experiment.parameters[1].conditions, Conditions)
    assert experiment.parameters[1].conditions['num_hidden_layers'] == ['1', '3']
    assert isinstance(experiment.metadata, Metadata)
    assert experiment.metadata['abc'] == 'def'
    assert experiment.metadata['ghi'] == 123
    assert experiment.folds == 10
    assert experiment.max_checkpoints == 9
    assert experiment.parallel_bandwidth == 2
    assert experiment.updated == 453
    assert experiment.user == '789'

    with warnings.catch_warnings(record=True) as w:
      assert experiment.can_be_deleted is None
      assert len(w) == 1
      assert issubclass(w[-1].category, DeprecationWarning)

    with warnings.catch_warnings(record=True) as w:
      assert experiment.parameters[0].tunable is None
      assert len(w) == 1
      assert issubclass(w[-1].category, DeprecationWarning)

    with warnings.catch_warnings(record=True) as w:
      experiment.progress.best_observation
      assert len(w) == 1
      assert issubclass(w[0].category, DeprecationWarning)
      assert 'best_assignments' in str(w[0].message)

    tasks_dict = {et.name: et.cost for et in experiment.tasks}
    assert tasks_dict == {'task 1': 0.567, 'task 2': 1.0}

  def test_mutable_experiment(self, experiment):
    experiment.name = 'other name'
    assert experiment.name == 'other name'
    assert experiment.to_json()['name'] == 'other name'

    experiment.parameters = [Parameter({})]
    assert len(experiment.parameters) == 1
    assert isinstance(experiment.parameters[0], Parameter)
    assert experiment.parameters[0].to_json() == {}
    assert experiment.to_json()['parameters'] == [{}]

    experiment.metadata = {'rst': 'zzz'}
    assert isinstance(experiment.metadata, Metadata)
    assert experiment.metadata['rst'] == 'zzz'
    assert experiment.metadata.get('abc') is None

  def test_del_experiment(self, experiment):
    assert experiment.name is not None
    assert experiment.parameters is not None
    assert experiment.metadata is not None
    del experiment.name
    del experiment.parameters
    del experiment.metadata
    assert experiment.name is None
    assert experiment.parameters is None
    assert experiment.metadata is None

  def test_client(self):
    client = load_and_parse(Client, 'client.json')
    assert isinstance(client, Client)
    assert client.id == '1'
    assert client.name == 'Client'
    assert client.created == 123

  def test_suggestion(self):
    suggestion = load_and_parse(Suggestion, 'suggestion.json')
    assert isinstance(suggestion, Suggestion)
    assert suggestion.id == '1'
    assert isinstance(suggestion.assignments, Assignments)
    assert suggestion.assignments.get('a') == 1
    assert suggestion.assignments.get('b') == 'c'
    assert suggestion.state == 'open'
    assert suggestion.experiment == '1'
    assert suggestion.created == 123
    assert isinstance(suggestion.metadata, Metadata)
    assert suggestion.metadata['abc'] == 'def'
    assert suggestion.metadata['ghi'] == 123
    assert suggestion.fold == '102'
    assert suggestion.fold_index == 3
    assert suggestion.checkpoint_index == 2
    assert suggestion.reference_id == '101'
    assert isinstance(suggestion.task, Task)
    assert suggestion.task.name == 'task 1'
    assert suggestion.task.cost == 0.567

  def test_pagination(self):
    pagination = Pagination(Experiment, load('pagination.json'))
    assert isinstance(pagination, Pagination)
    assert pagination.count == 2
    assert len(pagination.data) == 1
    assert isinstance(pagination.data[0], Experiment)
    assert isinstance(pagination.paging, Paging)
    assert pagination.paging.before == '1'
    assert pagination.paging.after == '2'

  def test_plan(self):
    plan = load_and_parse(Plan, 'plan.json')
    assert isinstance(plan, Plan)
    assert plan.id == 'premium'
    assert plan.name == 'SigOpt Premium'
    assert isinstance(plan.rules, PlanRules)
    assert plan.rules.max_dimension == 1
    assert plan.rules.max_experiments == 2
    assert plan.rules.max_observations == 3
    assert plan.rules.max_parallelism == 4
    assert isinstance(plan.current_period, PlanPeriod)
    assert plan.current_period.start == 0
    assert plan.current_period.end == 1000
    assert plan.current_period.experiments == ['1', '2']

  def test_token(self):
    token = load_and_parse(Token, 'token.json')
    assert isinstance(token, Token)
    assert token.all_experiments is False
    assert token.client == '456'
    assert token.development is True
    assert token.experiment == '1'
    assert token.expires == 1547139000
    assert token.permissions == 'read'
    assert token.token == '123'
    assert token.token_type == 'client-dev'
    assert token.user == '789'

  def test_metric(self):
    metric = load_and_parse(Metric, 'metric.json')
    assert isinstance(metric, Metric)
    assert metric.name == 'Test'
    assert metric.value_baseline == 0.4

  def test_importances(self):
    importances = load_and_parse(Importances, 'importances.json')
    assert isinstance(importances, Importances)
    assert isinstance(importances.importances, ImportancesMap)
    assert importances.importances['a'] == 0.92
    assert importances.importances['b'] == 0.03

  def test_metric_importances(self):
    metric_importances = load_and_parse(MetricImportances, 'metric_importances.json')
    assert isinstance(metric_importances, MetricImportances)
    assert isinstance(metric_importances.importances, ImportancesMap)
    assert metric_importances.importances['parameter_1'] == 0.92
    assert metric_importances.importances['parameter_2'] == 0.65
    assert metric_importances.importances['parameter_3'] == 0.03

  def test_organization(self):
    organization = load_and_parse(Organization, 'organization.json')
    assert isinstance(organization, Organization)
    assert organization.created == 123456
    assert organization.id == "7890"
    assert organization.name == "SigOpt"

  def test_task(self):
    task = load_and_parse(Task, 'task.json')
    assert isinstance(task, Task)
    assert task.name == 'task 1'
    assert task.cost == 0.567
