import mock
import pytest

from sigopt.interface import ConnectionImpl
from sigopt.requestor import Requestor

class TestEndpoint(object):
  @pytest.fixture
  def requestor(self):
    requestor = mock.Mock(Requestor)
    response = mock.Mock()
    response.status_code = 200
    response.json = mock.Mock(return_value={})
    requestor.request = mock.Mock(return_value=response)
    return requestor

  @pytest.fixture
  def connection(self, requestor):
    return ConnectionImpl(requestor)

  def assert_called(self, requestor, connection, method, url, params=None, headers=None, user_agent=None):
    params = params or {}
    if method in ('get', 'delete'):
      kwargs = {'params': params, 'json': None}
    else:
      kwargs = {'json': params, 'params': None}
    kwargs.update({'headers': headers})
    kwargs.update({'user_agent': user_agent})
    requestor.request.assert_called_once_with(
      method.upper(),
      'https://api.sigopt.com/v1' + url,
      **kwargs
    )

  def test_client_detail(self, requestor, connection):
    connection.clients(1).fetch()
    self.assert_called(requestor, connection, 'get', '/clients/1')

  def test_client_experiments(self, requestor, connection):
    connection.clients(1).experiments().fetch()
    self.assert_called(requestor, connection, 'get', '/clients/1/experiments')

  def test_experiment_list(self, requestor, connection):
    connection.experiments().fetch()
    self.assert_called(requestor, connection, 'get', '/experiments')

  def test_experiment_list_params(self, requestor, connection):
    connection.experiments().fetch(limit=10, before='1')
    self.assert_called(requestor, connection, 'get', '/experiments', {'limit': '10', 'before': '1'})

  def test_experiment_detail(self, requestor, connection):
    connection.experiments(1).fetch()
    self.assert_called(requestor, connection, 'get', '/experiments/1')

  def test_experiment_best_assignments(self, requestor, connection):
    connection.experiments(1).best_assignments().fetch()
    self.assert_called(requestor, connection, 'get', '/experiments/1/best_assignments')

  def test_experiment_importances(self, requestor, connection):
    connection.experiments(1).importances().fetch()
    self.assert_called(requestor, connection, 'get', '/experiments/1/importances')

  def test_experiment_metric_importances(self, requestor, connection):
    connection.experiments(1).metric_importances().fetch()
    self.assert_called(requestor, connection, 'get', '/experiments/1/metric_importances')

  def test_experiment_create(self, requestor, connection):
    connection.experiments().create()
    self.assert_called(requestor, connection, 'post', '/experiments')

  def test_experiment_create_params(self, requestor, connection):
    connection.experiments().create(name='Experiment', parameters=[])
    self.assert_called(requestor, connection, 'post', '/experiments', {'name': 'Experiment', 'parameters': []})

  def test_experiment_update(self, requestor, connection):
    connection.experiments(1).update()
    self.assert_called(requestor, connection, 'put', '/experiments/1')

  def test_experiment_delete(self, requestor, connection):
    connection.experiments(1).delete()
    self.assert_called(requestor, connection, 'delete', '/experiments/1')

  def test_suggestion_list(self, requestor, connection):
    connection.experiments(1).suggestions().fetch()
    self.assert_called(requestor, connection, 'get', '/experiments/1/suggestions')

  def test_suggestion_list_params(self, requestor, connection):
    connection.experiments(1).suggestions().fetch(limit=10, before='1')
    self.assert_called(requestor, connection, 'get', '/experiments/1/suggestions', {'limit': '10', 'before': '1'})

  def test_suggestion_detail(self, requestor, connection):
    connection.experiments(1).suggestions(2).fetch()
    self.assert_called(requestor, connection, 'get', '/experiments/1/suggestions/2')

  def test_suggestion_create(self, requestor, connection):
    connection.experiments(1).suggestions().create()
    self.assert_called(requestor, connection, 'post', '/experiments/1/suggestions')

  def test_suggestion_create_params(self, requestor, connection):
    connection.experiments(1).suggestions().create(assignments={'a': 1})
    self.assert_called(requestor, connection, 'post', '/experiments/1/suggestions', {'assignments': {'a': 1}})

  def test_suggestion_delete(self, requestor, connection):
    connection.experiments(1).suggestions(2).delete()
    self.assert_called(requestor, connection, 'delete', '/experiments/1/suggestions/2')

  def test_suggestion_delete_all(self, requestor, connection):
    connection.experiments(1).suggestions().delete()
    self.assert_called(requestor, connection, 'delete', '/experiments/1/suggestions')

  def test_suggestion_delete_all_params(self, requestor, connection):
    connection.experiments(1).suggestions().delete(state='open')
    self.assert_called(requestor, connection, 'delete', '/experiments/1/suggestions', {'state': 'open'})

  def test_queued_suggestion_list(self, requestor, connection):
    connection.experiments(1).queued_suggestions().fetch()
    self.assert_called(requestor, connection, 'get', '/experiments/1/queued_suggestions')

  def test_queued_suggestion_list_params(self, requestor, connection):
    connection.experiments(1).queued_suggestions().fetch(limit=10, before='1')
    self.assert_called(requestor, connection, 'get', '/experiments/1/queued_suggestions', {'limit': '10', 'before': '1'})

  def test_queued_suggestion_detail(self, requestor, connection):
    connection.experiments(1).queued_suggestions(2).fetch()
    self.assert_called(requestor, connection, 'get', '/experiments/1/queued_suggestions/2')

  def test_queued_suggestion_create_params(self, requestor, connection):
    connection.experiments(1).queued_suggestions().create(assignments={'a': 1})
    self.assert_called(requestor, connection, 'post', '/experiments/1/queued_suggestions', {'assignments': {'a': 1}})

  def test_queued_suggestion_delete(self, requestor, connection):
    connection.experiments(1).queued_suggestions(2).delete()
    self.assert_called(requestor, connection, 'delete', '/experiments/1/queued_suggestions/2')

  def test_observation_list(self, requestor, connection):
    connection.experiments(1).observations().fetch()
    self.assert_called(requestor, connection, 'get', '/experiments/1/observations')

  def test_observation_list_params(self, requestor, connection):
    connection.experiments(1).observations().fetch(limit=10, before='1')
    self.assert_called(requestor, connection, 'get', '/experiments/1/observations', {'limit': '10', 'before': '1'})

  def test_observation_detail(self, requestor, connection):
    connection.experiments(1).observations(2).fetch()
    self.assert_called(requestor, connection, 'get', '/experiments/1/observations/2')

  def test_observation_create(self, requestor, connection):
    connection.experiments(1).observations().create()
    self.assert_called(requestor, connection, 'post', '/experiments/1/observations')

  def test_observation_create_params(self, requestor, connection):
    connection.experiments(1).observations().create(assignments={'a': 1})
    self.assert_called(requestor, connection, 'post', '/experiments/1/observations', {'assignments': {'a': 1}})

  def test_observation_create_batch(self, requestor, connection):
    connection.experiments(1).observations().create_batch()
    self.assert_called(requestor, connection, 'post', '/experiments/1/observations/batch')

  def test_observation_update(self, requestor, connection):
    connection.experiments(1).observations(2).update()
    self.assert_called(requestor, connection, 'put', '/experiments/1/observations/2')

  def test_observation_update_params(self, requestor, connection):
    connection.experiments(1).observations(2).update(value=5)
    self.assert_called(requestor, connection, 'put', '/experiments/1/observations/2', {'value': 5})

  def test_observation_delete(self, requestor, connection):
    connection.experiments(1).observations(2).delete()
    self.assert_called(requestor, connection, 'delete', '/experiments/1/observations/2')

  def test_observation_delete_all(self, requestor, connection):
    connection.experiments(1).observations().delete()
    self.assert_called(requestor, connection, 'delete', '/experiments/1/observations')

  def test_token_create(self, requestor, connection):
    connection.experiments(1).tokens().create()
    self.assert_called(requestor, connection, 'post', '/experiments/1/tokens')

  def test_call_with_json(self, requestor, connection):
    connection.experiments(1).tokens().create.call_with_json('{}')
    self.assert_called(requestor, connection, 'post', '/experiments/1/tokens')

  def test_call_with_json_params(self, requestor, connection):
    connection.experiments(1).tokens().create.call_with_json('{"value": 5}')
    self.assert_called(requestor, connection, 'post', '/experiments/1/tokens', {'value': 5})

  def test_call_with_params(self, requestor, connection):
    connection.experiments(1).tokens().create.call_with_params({})
    self.assert_called(requestor, connection, 'post', '/experiments/1/tokens')

  def test_call_with_params_params(self, requestor, connection):
    connection.experiments(1).tokens().create.call_with_params({'value': 5})
    self.assert_called(requestor, connection, 'post', '/experiments/1/tokens', {'value': 5})

  def test_organizations_list(self, requestor, connection):
    connection.organizations().fetch()
    self.assert_called(requestor, connection, 'get', '/organizations')

  def test_organization_details(self, requestor, connection):
    connection.organizations(1).fetch()
    self.assert_called(requestor, connection, 'get', '/organizations/1')
