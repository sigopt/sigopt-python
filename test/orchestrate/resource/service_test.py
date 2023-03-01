# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import os

import pytest

from sigopt.orchestrate.resource.service import ResourceService


TEST_MODULE = 'test'
TEST_FILE = 'test_file.txt'
ACTUAL_TEXT = "This is a test file for testing the resource service.\n".encode()

class TestResourceService(object):
  @pytest.fixture
  def resource_service(self):
    return ResourceService(None)

  def test_resource_stream(self, resource_service):
    with resource_service.stream(TEST_MODULE, TEST_FILE) as stream:
      assert ACTUAL_TEXT == stream.read()

  def test_resource_open(self, resource_service):
    with resource_service.open(TEST_MODULE, TEST_FILE) as test_fp:
      assert ACTUAL_TEXT == test_fp.read()
      with open(test_fp.name, mode='rb') as second_open:
        assert ACTUAL_TEXT == second_open.read()

  def test_tempfile_removed(self, resource_service):
    test_fp = resource_service.open(TEST_MODULE, TEST_FILE)
    test_fp.close()
    assert not os.path.isfile(test_fp.name)

  def test_resource_read(self, resource_service):
    assert ACTUAL_TEXT == resource_service.read(TEST_MODULE, TEST_FILE)
