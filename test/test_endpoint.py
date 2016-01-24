import mock
import pytest

from sigopt.interface import Connection
from sigopt.requestor import Requestor

class TestEndpoint(object):
  @pytest.fixture
  def connection(self):
    requestor = mock.Mock(Requestor)
    connection = Connection('client_token')
    connection.requestor = requestor
    response = mock.Mock()
    response.status_code = 200
    response.json = mock.Mock(return_value={})
    connection.requestor.get = mock.Mock(return_value=response)
    connection.requestor.post = mock.Mock(return_value=response)
    connection.requestor.put = mock.Mock(return_value=response)
    connection.requestor.delete = mock.Mock(return_value=response)
    return connection

  def assert_called(self, connection, method, url, params=None):
    params = params or {}
    if method in ('put', 'post'):
      kwargs = {'json': params}
    else:
      kwargs = {'params': params}
    getattr(connection.requestor, method).assert_called_once_with(
      'https://api.sigopt.com/v1' + url,
      headers=mock.ANY,
      **kwargs
    )

  def test_client_detail(self, connection):
    connection.clients(1).fetch()
    self.assert_called(connection, 'get', '/clients/1')

  def test_experiment_list(self, connection):
    connection.experiments().fetch()
    self.assert_called(connection, 'get', '/experiments')

  def test_experiment_list_params(self, connection):
    connection.experiments().fetch(limit=10, before='1')
    self.assert_called(connection, 'get', '/experiments', {'limit': '10', 'before': '1'})

  def test_experiment_detail(self, connection):
    connection.experiments(1).fetch()
    self.assert_called(connection, 'get', '/experiments/1')

  def test_experiment_create(self, connection):
    connection.experiments().create()
    self.assert_called(connection, 'post', '/experiments')

  def test_experiment_create_params(self, connection):
    connection.experiments().create(name='Experiment', parameters=[])
    self.assert_called(connection, 'post', '/experiments', {'name': 'Experiment', 'parameters': []})

  def test_experiment_update(self, connection):
    connection.experiments(1).update()
    self.assert_called(connection, 'put', '/experiments/1')

  def test_experiment_delete(self, connection):
    connection.experiments(1).delete()
    self.assert_called(connection, 'delete', '/experiments/1')

  def test_suggestion_list(self, connection):
    connection.experiments(1).suggestions().fetch()
    self.assert_called(connection, 'get', '/experiments/1/suggestions')

  def test_suggestion_list_params(self, connection):
    connection.experiments(1).suggestions().fetch(limit=10, before='1')
    self.assert_called(connection, 'get', '/experiments/1/suggestions', {'limit': '10', 'before': '1'})

  def test_suggestion_detail(self, connection):
    connection.experiments(1).suggestions(2).fetch()
    self.assert_called(connection, 'get', '/experiments/1/suggestions/2')

  def test_suggestion_create(self, connection):
    connection.experiments(1).suggestions().create()
    self.assert_called(connection, 'post', '/experiments/1/suggestions')

  def test_suggestion_create_params(self, connection):
    connection.experiments(1).suggestions().create(assignments={'a': 1})
    self.assert_called(connection, 'post', '/experiments/1/suggestions', {'assignments': {'a': 1}})

  def test_suggestion_delete(self, connection):
    connection.experiments(1).suggestions(2).delete()
    self.assert_called(connection, 'delete', '/experiments/1/suggestions/2')

  def test_suggestion_delete_all(self, connection):
    connection.experiments(1).suggestions().delete()
    self.assert_called(connection, 'delete', '/experiments/1/suggestions')

  def test_suggestion_delete_all_params(self, connection):
    connection.experiments(1).suggestions().delete(state='open')
    self.assert_called(connection, 'delete', '/experiments/1/suggestions', {'state': 'open'})

  def test_observation_list(self, connection):
    connection.experiments(1).observations().fetch()
    self.assert_called(connection, 'get', '/experiments/1/observations')

  def test_observation_list_params(self, connection):
    connection.experiments(1).observations().fetch(limit=10, before='1')
    self.assert_called(connection, 'get', '/experiments/1/observations', {'limit': '10', 'before': '1'})

  def test_observation_detail(self, connection):
    connection.experiments(1).observations(2).fetch()
    self.assert_called(connection, 'get', '/experiments/1/observations/2')

  def test_observation_create(self, connection):
    connection.experiments(1).observations().create()
    self.assert_called(connection, 'post', '/experiments/1/observations')

  def test_observation_create_params(self, connection):
    connection.experiments(1).observations().create(assignments={'a': 1})
    self.assert_called(connection, 'post', '/experiments/1/observations', {'assignments': {'a': 1}})

  def test_observation_update(self, connection):
    connection.experiments(1).observations(2).update()
    self.assert_called(connection, 'put', '/experiments/1/observations/2')

  def test_observation_update_params(self, connection):
    connection.experiments(1).observations(2).update(value=5)
    self.assert_called(connection, 'put', '/experiments/1/observations/2', {'value': 5})

  def test_observation_delete(self, connection):
    connection.experiments(1).observations(2).delete()
    self.assert_called(connection, 'delete', '/experiments/1/observations/2')

  def test_observation_delete_all(self, connection):
    connection.experiments(1).observations().delete()
    self.assert_called(connection, 'delete', '/experiments/1/observations')
