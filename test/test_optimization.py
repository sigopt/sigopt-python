import mock
import pytest

from sigopt.optimization import optimization_loop
from .utils import ObserveWarnings


class TestOptimizationLoop(object):
  @pytest.fixture
  def connection_with_budget_two(self):
    budget = 2
    experiment_mocks = [
      mock.Mock(
        progress=mock.Mock(
          observation_budget_consumed=i,
        ),
        observation_budget=budget,
      )
      for i in range(budget + 1)
    ]
    connection = mock.Mock()
    experiment_resource = mock.Mock(
      fetch=mock.Mock(side_effect=experiment_mocks),
    )
    connection.experiments = mock.Mock(return_value=experiment_resource)
    return connection

  def test_optimization_loop(self, connection_with_budget_two):
    loop_body = mock.Mock()
    connection = connection_with_budget_two
    experiment = connection.experiments('123').fetch()
    optimization_loop(connection, experiment, loop_body)
    assert loop_body.call_count == 2

  def test_optimization_loop_with_exceptions(self, connection_with_budget_two):
    loop_body = mock.Mock(
      side_effect=[
        Exception('Test exception')
        for _ in range(2)
      ],
    )
    connection = connection_with_budget_two
    experiment = connection.experiments('123').fetch()
    with ObserveWarnings() as w:
      optimization_loop(connection, experiment, loop_body)
      assert len(w) >= 1
      assert issubclass(w[-1].category, RuntimeWarning)
    assert loop_body.call_count == 2
