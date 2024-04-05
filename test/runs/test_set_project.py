# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import mock
import pytest
import warnings

from sigopt import _global_factory, set_project


def test_set_project_with_global_run():
  with mock.patch("sigopt.get_run_id", mock.Mock(return_value="1")):
    with pytest.warns(UserWarning):
      set_project("test-123")
  assert _global_factory.project == "test-123"


def test_set_project_without_run():
  with mock.patch("sigopt.get_run_id", mock.Mock(return_value=None)):
    with warnings.catch_warnings():
      warnings.simplefilter("error")
      set_project("test-123")
  assert _global_factory.project == "test-123"
