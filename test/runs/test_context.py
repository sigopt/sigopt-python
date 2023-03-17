# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from __future__ import print_function
import mock
import pytest

from sigopt.interface import Connection
from sigopt.run_context import allow_state_update, RunContext


@pytest.mark.parametrize(
  "new_state,old_state,expected",
  [
    ("completed", "active", True),
    ("failed", "active", True),
    ("completed", "completed", False),
    ("failed", "completed", True),
    ("completed", "failed", False),
    ("failed", "failed", False),
  ],
)
def test_allow_state_update(new_state, old_state, expected):
  assert allow_state_update(new_state, old_state) == expected


class TestLiveRunContext(object):
  def make_run_context(self):
    mock_driver = mock.Mock()
    mock_driver.request = mock.Mock(side_effect=[None])
    run_context = RunContext(
      connection=Connection(driver=mock_driver),
      run=mock.Mock(id="0", assignments={"fixed1": 0, "fixed2": "test"}),
    )
    return run_context

  @pytest.fixture
  def run_context(self):
    return self.make_run_context()

  def assert_run_update_request_called(self, run_context, data):
    run_context.connection.impl.driver.request.assert_called_once_with(
      "MERGE", ["training_runs", "0"], data, {"X-Response-Content": "skip"}
    )

  @pytest.mark.parametrize(
    "test_value",
    [
      12345,
      1.2345,
      "hello",
    ],
  )
  def test_assignment_setitem(self, run_context, test_value):
    test_key = "assignment_test_key"
    run_context.params[test_key] = test_value
    assert run_context.params[test_key] == test_value
    assert getattr(run_context.params, test_key) == test_value
    self.assert_run_update_request_called(
      run_context, {"assignments": {test_key: test_value}}
    )

  @pytest.mark.parametrize(
    "test_value",
    [
      12345,
      1.2345,
      "hello",
    ],
  )
  def test_assignment_setattr(self, run_context, test_value):
    test_key = "assignment_test_key"
    setattr(run_context.params, test_key, test_value)
    assert run_context.params[test_key] == test_value
    assert getattr(run_context.params, test_key) == test_value
    self.assert_run_update_request_called(
      run_context, {"assignments": {test_key: test_value}}
    )

  def test_log_failure_method(self, run_context):
    return_value = run_context.log_failure()
    assert return_value is None
    self.assert_run_update_request_called(run_context, {"state": "failed"})

  @pytest.mark.parametrize(
    "test_value",
    [
      12345,
      1.2345,
    ],
  )
  def test_log_metadata_method_with_numbers(self, run_context, test_value):
    test_key = "test_metadata_key"
    return_value = run_context.log_metadata(test_key, test_value)
    assert return_value is None
    self.assert_run_update_request_called(
      run_context, {"metadata": {test_key: test_value}}
    )

  def test_log_metadata_method_with_null(self, run_context):
    test_key = "test_metadata_key"
    return_value = run_context.log_metadata(test_key, None)
    assert return_value is None
    self.assert_run_update_request_called(run_context, {"metadata": {test_key: None}})

  @pytest.mark.parametrize(
    "test_value",
    [
      "hello",
      [],
      {},
      object(),
    ],
  )
  def test_log_metadata_method_stringifies_objects(self, run_context, test_value):
    test_key = "test_metadata_key"
    return_value = run_context.log_metadata(test_key, test_value)
    assert return_value is None
    self.assert_run_update_request_called(
      run_context, {"metadata": {test_key: str(test_value)}}
    )

  @pytest.mark.parametrize(
    "test_value",
    [
      12345,
      1.2345,
    ],
  )
  def test_log_metric_method_good_value(self, run_context, test_value):
    test_key = "test_metric_key"
    return_value = run_context.log_metric(test_key, test_value)
    assert return_value is None
    self.assert_run_update_request_called(
      run_context,
      {
        "values": {
          test_key: {"value": test_value},
        }
      },
    )

  @pytest.mark.parametrize(
    "test_value",
    [
      None,
      "hello",
      [],
      {},
      object(),
    ],
  )
  def test_log_metric_method_bad_value(self, run_context, test_value):
    test_key = "test_metric_key"
    with pytest.raises(ValueError):
      run_context.log_metric(test_key, test_value)

  @pytest.mark.parametrize(
    "test_stddev",
    [
      12345,
      1.2345,
    ],
  )
  def test_log_metric_method_good_stddev(self, run_context, test_stddev):
    test_key = "test_metric_key"
    test_value = 0
    return_value = run_context.log_metric(test_key, test_value, test_stddev)
    assert return_value is None
    self.assert_run_update_request_called(
      run_context,
      {
        "values": {
          test_key: {
            "value": test_value,
            "value_stddev": test_stddev,
          },
        }
      },
    )

  @pytest.mark.parametrize(
    "test_stddev",
    [
      "hello",
      [],
      {},
      object(),
    ],
  )
  def test_log_metric_method_bad_stddev(self, run_context, test_stddev):
    test_key = "test_metric_key"
    test_value = 0
    with pytest.raises(ValueError):
      run_context.log_metric(test_key, test_value, test_stddev)

  def test_log_dataset(self, run_context):
    dataset_name = "dataset for testing"
    return_value = run_context.log_dataset(
      name=dataset_name,
    )
    assert return_value is None
    self.assert_run_update_request_called(
      run_context,
      {
        "datasets": {
          dataset_name: {},
        }
      },
    )

  def test_log_model(self, run_context):
    model_type = "test type"
    return_value = run_context.log_model(type=model_type)
    assert return_value is None
    self.assert_run_update_request_called(run_context, {"model": {"type": model_type}})
