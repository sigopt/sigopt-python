import mock
import pytest

from sigopt import set_project, _global_factory

def test_set_project_with_global_run():
  with mock.patch("sigopt.get_run_id", mock.Mock(return_value="1")):
    with pytest.warns(UserWarning):
      set_project("test-123")
  assert _global_factory.project == "test-123"

def test_set_project_without_run():
  with mock.patch("sigopt.get_run_id", mock.Mock(return_value=None)):
    with pytest.warns(None) as warnings:
      set_project("test-123")
  assert len(warnings) == 0
  assert _global_factory.project == "test-123"
