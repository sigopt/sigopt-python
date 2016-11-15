import pytest
import warnings

from sigopt.objects import *

warnings.simplefilter("always")

class TestBase(object):
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
    assert repr(Experiment({})) == 'Experiment({})'
    assert repr(Experiment({'a': 'b'})) == 'Experiment({\n  "a": "b"\n})'
    assert repr(Assignments({})) == 'Assignments({})'
    assert repr(Assignments({'a': 'b'})) == 'Assignments({\n  "a": "b"\n})'
    assert repr(Assignments({'a': 'b', 'c': 'd'})) == 'Assignments({\n  "a": "b",\n  "c": "d"\n})'
    assert repr(Bounds({'a': 'b'})) == 'Bounds({\n  "a": "b"\n})'

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
    return Experiment({
      'object': 'experiment',
      'id': '123',
      'name': 'Test Experiment',
      'type': 'cross_validated',
      'folds': 10,
      'created': 321,
      'state': 'active',
      'metrics': [
        {
          'object': 'metric',
          'name': 'Revenue',
        },
        {
          'object': 'metric',
          'name': 'Sales',
        },
      ],
      'client': '678',
      'progress': {
        'object': 'progress',
        'observation_count': 3,
        'first_observation': {
          'object': 'observation',
          'id': '1',
          'assignments': {
            'a': 1,
            'b': 'c',
          },
          'values': [
            {
              'object': 'value',
              'name': 'Revenue',
              'value': 3.1,
              'value_stddev': None,
            },
            {
              'object': 'value',
              'name': 'Sales',
              'value': 2.5,
              'value_stddev': None,
            }
          ],
          'failed': False,
          'created': 451,
          'suggestion': '11',
          'experiment': '123',
        },
        'last_observation': {
          'object': 'observation',
          'id': '2',
          'assignments': {
            'a': 2,
            'b': 'd',
          },
          'values': [
            {
              'object': 'value',
              'name': 'Revenue',
              'value': 3.1,
              'value_stddev': 0.5,
            },
            {
              'object': 'value',
              'name': 'Sales',
              'value': 2.5,
              'value_stddev': 0.8,
            }
          ],
          'failed': False,
          'created': 452,
          'suggestion': '12',
          'experiment': '123',
        },
        'best_observation': {
          'object': 'observation',
          'id': '3',
          'assignments': {
            'a': 3,
            'b': 'd',
          },
          'values': [
            {
              'object': 'value',
              'name': 'Revenue',
              'value': None,
              'value_stddev': None,
            },
            {
              'object': 'value',
              'name': 'Sales',
              'value': None,
              'value_stddev': None,
            }
          ],
          'failed': True,
          'created': 453,
          'suggestion': '13',
          'experiment': '123',
          'metadata': {
            'abc': 'def',
            'ghi': 123,
          },
        },
      },
      'parameters': [
        {
          'object': 'parameter',
          'name': 'a',
          'type': 'double',
          'bounds': {
            'object': 'bounds',
            'min': 1,
            'max': 2,
          },
          'categorical_values': None,
          'precision': 3,
          'default_value': 2,
        },
        {
          'object': 'parameter',
          'name': 'b',
          'type': 'categorical',
          'bounds': None,
          'categorical_values': [
            {'name': 'c', 'enum_index': 1},
            {'name': 'd', 'enum_index': 2},
          ],
          'precision': None,
          'default_value': None,
        },
      ],
      'metadata': {
        'abc': 'def',
        'ghi': 123,
      },
    })

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
    assert isinstance(experiment.progress, Progress)
    assert experiment.progress.observation_count == 3
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
    assert isinstance(experiment.metadata, Metadata)
    assert experiment.metadata['abc'] == 'def'
    assert experiment.metadata['ghi'] == 123
    assert experiment.folds == 10

    with warnings.catch_warnings(record=True) as w:
      assert experiment.can_be_deleted is None
      assert len(w) == 1
      assert issubclass(w[-1].category, DeprecationWarning)

    with warnings.catch_warnings(record=True) as w:
      assert experiment.parameters[0].tunable is None
      assert len(w) == 1
      assert issubclass(w[-1].category, DeprecationWarning)

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
    client = Client({
      'object': 'client',
      'id': '1',
      'name': 'Client',
      'created': 123,
    })
    assert isinstance(client, Client)
    assert client.id == '1'
    assert client.name == 'Client'
    assert client.created == 123

  def test_suggestion(self):
    suggestion = Suggestion({
      'object': 'suggestion',
      'id': '1',
      'assignments': {
        'a': 1,
        'b': 'c',
      },
      'state': 'open',
      'experiment': '1',
      'created': 123,
      'fold_index': 2,
      'metadata': {
        'abc': 'def',
        'ghi': 123,
      },
    })
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
    assert suggestion.fold_index == 2

  def test_pagination(self):
    experiment = Experiment({'object': 'experiment'})
    pagination = Pagination(Experiment, {
      'object': 'pagination',
      'count': 2,
      'data': [experiment.to_json()],
      'paging': {
        'before': '1',
        'after': '2',
      },
    })
    assert isinstance(pagination, Pagination)
    assert pagination.count == 2
    assert len(pagination.data) == 1
    assert isinstance(pagination.data[0], Experiment)
    assert pagination.data[0] == experiment
    assert isinstance(pagination.paging, Paging)
    assert pagination.paging.before == '1'
    assert pagination.paging.after == '2'

  def test_plan(self):
    plan = Plan({
      'object': 'plan',
      'id': 'premium',
      'name': 'SigOpt Premium',
      'rules': {
        'max_dimension': 1,
        'max_experiments': 2,
        'max_observations': 3,
        'max_parallelism': 4,
      },
      'current_period': {
        'start': 0,
        'end': 1000,
        'experiments': [
          '1',
          '2',
        ],
      },
    })

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
    token = Token({
      'all_experiments': False,
      'development': True,
      'permissions': 'read',
      'token': '123',
      'client': '456',
      'experiment': '1',
      'user': '789',
    })

    assert isinstance(token, Token)
    assert token.all_experiments is False
    assert token.development is True
    assert token.permissions == 'read'
    assert token.token == '123'
    assert token.client == '456'
    assert token.experiment == '1'
    assert token.user == '789'
