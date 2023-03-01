# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import pytest

from sigopt.urllib3_patch import ExpiringHTTPConnectionPool, ExpiringHTTPSConnectionPool

@pytest.mark.parametrize("pool_cls", [ExpiringHTTPConnectionPool, ExpiringHTTPSConnectionPool])
def test_pool_reuses_connections(pool_cls):
  pool = pool_cls(host="sigopt.com", expiration_seconds=30)
  conn1 = pool._get_conn()
  pool._put_conn(conn1)
  conn2 = pool._get_conn()
  assert conn1 is conn2

@pytest.mark.parametrize("pool_cls", [ExpiringHTTPConnectionPool, ExpiringHTTPSConnectionPool])
def test_pool_expires_connections(pool_cls):
  pool = pool_cls(host="sigopt.com", expiration_seconds=0)
  conn1 = pool._get_conn()
  pool._put_conn(conn1)
  conn2 = pool._get_conn()
  assert conn1 is not conn2
