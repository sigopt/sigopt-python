# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from __future__ import print_function

import base64
import errno
import json
import os

from .paths import get_root_subdir


class UserAgentInfoContext(object):
  CONFIG_CONTEXT_KEY = "user_agent_info"

  @classmethod
  def from_config(cls, _config):
    return cls(_config.get_context_data(cls))

  def __init__(self, info):
    self.info = info

  def to_json(self):
    return self.info


class Config(object):
  API_TOKEN_KEY = "api_token"
  CELL_TRACKING_ENABLED_KEY = "code_tracking_enabled"
  LOG_COLLECTION_ENABLED_KEY = "log_collection_enabled"
  CONTEXT_ENVIRONMENT_KEY = "SIGOPT_CONTEXT"

  def __init__(self):
    self._config_json_path = os.path.abspath(
      os.path.join(
        get_root_subdir("client"),
        "config.json",
      )
    )
    self._configuration = self._read_config_json()
    self._json_context = {}
    try:
      encoded_context = os.environ[self.CONTEXT_ENVIRONMENT_KEY]
    except KeyError:
      pass
    else:
      decoded = base64.b64decode(encoded_context).decode("utf-8")
      self._json_context = json.loads(decoded)
    self._object_context = {}

  @property
  def config_json_path(self):
    return self._config_json_path

  def get_context_data(self, entry_cls):
    key = entry_cls.CONFIG_CONTEXT_KEY
    instance = self._object_context.get(key)
    if instance:
      return instance.to_json()
    return self._json_context.get(key)

  def set_context_entry(self, entry):
    self._object_context[entry.CONFIG_CONTEXT_KEY] = entry

  def get_environment_context(self):
    context = dict(self._json_context)
    for key, value in self._object_context.items():
      context[key] = value.to_json()
    return {self.CONTEXT_ENVIRONMENT_KEY: base64.b64encode(json.dumps(context).encode())}

  @property
  def api_token(self):
    return self._configuration.get(self.API_TOKEN_KEY)

  @property
  def cell_tracking_enabled(self):
    return self._configuration.get(self.CELL_TRACKING_ENABLED_KEY, False)

  @property
  def log_collection_enabled(self):
    return self._configuration.get(self.LOG_COLLECTION_ENABLED_KEY, False)

  def _ensure_config_json_path(self):
    config_path = self._config_json_path
    try:
      os.makedirs(os.path.dirname(config_path))
    except OSError as e:
      if e.errno != errno.EEXIST:
        raise
    return config_path

  def _read_config_json(self):
    try:
      with open(self._config_json_path) as config_json_fp:
        return json.load(config_json_fp)
    except (IOError, OSError) as e:
      if e.errno == errno.ENOENT:
        return {}
      raise

  def _write_config_json(self, configuration):
    config_path = self._ensure_config_json_path()
    with open(config_path, "w") as config_json_fp:
      json.dump(configuration, config_json_fp, indent=2, sort_keys=True)
      print("", file=config_json_fp)

  def persist_configuration_options(self, options):
    self._configuration.update(options)
    self._write_config_json(self._configuration)

  def set_user_agent_info(self, info):
    self.set_context_entry(UserAgentInfoContext(info))

  def get_user_agent_info(self):
    return UserAgentInfoContext.from_config(self).info


config = Config()
