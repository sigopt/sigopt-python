# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import mock
import pytest
from contextlib import contextmanager
import warnings

import sigopt
from sigopt.exception import RunException
from sigopt.run_context import RunContext, GlobalRunContext
from sigopt.factory import SigOptFactory


warnings.simplefilter("always")


class TestSigOptFactory(object):
  @pytest.fixture
  def api_connection(self):
    conn = mock.Mock()
    conn.clients().projects().training_runs().create.return_value = mock.Mock(assignments={"fixed1": 0, "fixed2": "test"})
    return conn

  @pytest.fixture(autouse=True)
  def patched_connection(self, api_connection):
    with mock.patch('sigopt.factory.get_connection') as connection_singleton:
      connection_singleton.return_value = api_connection
      yield

  @pytest.fixture
  def factory(self):
    factory = SigOptFactory("test-project")
    return factory

  def test_create_run(self, factory):
    run_context = factory.create_run()
    assert run_context is not None

  def test_create_context_with_name(self, factory, api_connection):
    run_context = factory.create_run(name='test context')
    assert run_context is not None
    api_connection.clients().projects().training_runs().create.assert_called_once()
    assert api_connection.clients().projects().training_runs().create.call_args[1]['name'] == 'test context'

  def test_local_run_context_methods(self, factory):
    with factory.create_run(name='test-run') as local_run:
      local_run._update_run = mock.Mock()
      local_run.params.p1 = 1
      local_run.params.setdefault("p2", 2)
      local_run.params.update({"p3": 3, "p4": 4})
      local_run.params.setdefault("p3", 0)
      local_run.params.pop("p2")
      local_run.log_metric('metric', 1, 0.1)
    local_run._update_run.assert_has_calls([
      mock.call({'assignments': {'p1': 1}}),
      mock.call({'assignments': {'p2': 2}}),
      mock.call({'assignments': {'p3': 3, 'p4': 4}}),
      mock.call({'assignments': {'p2': None}}),
      mock.call({'values': {'metric': {'value': 1, 'value_stddev': 0.1}}}),
      mock.call({'state': 'completed'}),
    ])

  def test_local_run_context_exception(self, factory):

    class TestException(Exception):
      pass

    with pytest.raises(TestException):
      with factory.create_run(name='test-run') as local_run:
        local_run._update_run = mock.Mock()
        raise TestException()
    local_run._update_run.assert_has_calls([
      mock.call({'state': 'failed'}),
    ])
