# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import base64
import mock
import os

from sigopt.config import Config

fake_context = base64.b64encode(b'{"a": "b"}').decode('utf-8')

class FakeConfigContext(object):
  def __init__(self, key):
    self.CONFIG_CONTEXT_KEY = key

class TestConfig(object):
  def test_load_json_config(self):
    with mock.patch.dict(os.environ, {'SIGOPT_CONTEXT': fake_context}):
      config = Config()

    assert config.get_context_data(FakeConfigContext('a')) == 'b'
    assert config.get_context_data(FakeConfigContext('none')) is None
