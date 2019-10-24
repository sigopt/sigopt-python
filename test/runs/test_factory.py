import mock
import pytest
from contextlib import contextmanager
import warnings

import sigopt
from sigopt.exception import RunException
from sigopt.runs.context import LiveRunContext, NullRunContext
from sigopt.runs.factory import RunFactory


warnings.simplefilter("always")


class TestRunFactory(object):
  @pytest.fixture
  def api_connection(self):
    return mock.Mock()

  @pytest.yield_fixture
  def patched_factory_class(self, api_connection):
    with mock.patch('sigopt.runs.factory.RunFactory._get_connection_singleton') as connection_singleton:
      connection_singleton.return_value = api_connection
      yield

  @pytest.fixture
  def run_factory(self, patched_factory_class):
    return RunFactory()

  def test_create_run(self, run_factory):
    run_context = run_factory.create_run()
    assert run_context is not None
    assert run_context.connection == run_factory.connection

  def test_create_context_with_name_and_project(self, run_factory, api_connection):
    run_context = run_factory.create_run(name='test context', project='test-project')
    assert run_context is not None
    assert run_context.connection == run_factory.connection
    api_connection.tokens.assert_called_once()
    api_connection.clients().projects().create.assert_called_once()
    assert api_connection.clients().projects().create.call_args[1]['name'] == 'test-project'
    api_connection.clients().projects().training_runs().create.assert_called_once()
    assert api_connection.clients().projects().training_runs().create.call_args[1]['name'] == 'test context'

  def test_returns_global_null_context(self, run_factory):
    context = run_factory.get_global_run_context()
    assert isinstance(context, NullRunContext)

  def test_local_run_context_methods(self, run_factory):
    with mock.patch('sigopt.runs.RunFactoryProxyMethod.instance', run_factory):
      with run_factory.create_run(name='test-run', project='test-project') as local_run:
        assert isinstance(local_run, LiveRunContext)
        local_run._update_run = mock.Mock()
        assert local_run.get_parameter('assignment', 1) == 1
        local_run.log_metric('metric', 1, 0.1)
    local_run._update_run.assert_has_calls([
      mock.call({'assignments': {'assignment': 1}}),
      mock.call({'values': {'metric': {'value': 1, 'value_stddev': 0.1}}}),
      mock.call({'state': 'completed'}),
    ])

  def test_local_run_context_exception(self, run_factory):

    class TestException(Exception):
      pass

    with mock.patch('sigopt.runs.RunFactoryProxyMethod.instance', run_factory):
      with pytest.raises(TestException):
        with run_factory.create_run(name='test-run', project='test-project') as local_run:
          assert isinstance(local_run, LiveRunContext)
          local_run._update_run = mock.Mock()
          raise TestException()
    local_run._update_run.assert_has_calls([
      mock.call({'state': 'failed'}),
    ])

  def test_live_global_context(self, run_factory):
    with mock.patch('sigopt.runs.RunFactoryProxyMethod.instance', run_factory):
      with run_factory.create_global_run(name='test-run', project='test-project') as global_run:
        assert isinstance(global_run, LiveRunContext)
        factory_global_run = run_factory.get_global_run_context()
        assert factory_global_run is global_run

  def test_sigopt_methods_global_run_context(self, run_factory):
    with mock.patch('sigopt.runs.RunFactoryProxyMethod.instance', run_factory):
      with run_factory.create_global_run(name='test-run', project='test-project') as global_run:
        global_run._update_run = mock.Mock()
        assert sigopt.get_parameter('assignment', 1) == 1
        sigopt.log_metric('metric', 1, 0.1)
    global_run._update_run.assert_has_calls([
      mock.call({'assignments': {'assignment': 1}}),
      mock.call({'values': {'metric': {'value': 1, 'value_stddev': 0.1}}}),
      mock.call({'state': 'completed'}),
    ])

  def test_exception_global_run_context(self, run_factory):

    class TestException(Exception):
      pass

    with mock.patch('sigopt.runs.RunFactoryProxyMethod.instance', run_factory):
      with pytest.raises(TestException):
        with run_factory.create_global_run(name='test-run', project='test-project') as global_run:
          global_run._update_run = mock.Mock()
          raise TestException()
    global_run._update_run.assert_has_calls([
      mock.call({'state': 'failed'}),
    ])
