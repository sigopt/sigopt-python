# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import logging
import time

from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool

logger = logging.getLogger("sigopt.urllib3_patch")

class SigOptHTTPConnection(HTTPConnection):
  """
  Tracks the time since the last activity of the connection.
  """

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.reset_activity()

  def reset_activity(self):
    self.last_activity = time.time()

  def request(self, *args, **kwargs):
    super().request(*args, **kwargs)
    self.reset_activity()

  def request_chunked(self, *args, **kwargs):
    super().request_chunked(*args, **kwargs)
    self.reset_activity()

  def close(self, *args, **kwargs):
    super().close()
    self.reset_activity()

class SigOptHTTPSConnection(SigOptHTTPConnection, HTTPSConnection):
  pass

class ExpiringHTTPConnectionPool(HTTPConnectionPool):
  """
  Returns a new connection when the time since the connection was last used is greater than the expiration time.
  """

  ConnectionCls = SigOptHTTPConnection

  def __init__(self, *args, expiration_seconds=30, **kwargs):
    super().__init__(*args, **kwargs)
    self.expiration_seconds = expiration_seconds

  def _get_conn(self, timeout=None):
    conn = super()._get_conn(timeout=timeout)
    if time.time() - conn.last_activity > self.expiration_seconds:
      logger.debug("Abandoning expired connection")
      return self._new_conn()
    return conn

class ExpiringHTTPSConnectionPool(ExpiringHTTPConnectionPool, HTTPSConnectionPool):
  ConnectionCls = SigOptHTTPSConnection
