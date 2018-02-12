import os
import pytest
import mock

from sigopt.interface import Connection
from sigopt.resource import ApiResource

class TestInterface(object):
  def test_create(self):
    conn = Connection(client_token='client_token')
    assert conn.impl.api_url == 'https://api.sigopt.com'
    assert conn.impl.requestor.verify_ssl_certs is True
    assert conn.impl.requestor.proxies is None
    assert isinstance(conn.clients, ApiResource)
    assert isinstance(conn.experiments, ApiResource)

  def test_environment_variable(self):
    with mock.patch.dict(os.environ, {'SIGOPT_API_TOKEN': 'client_token'}):
      Connection()

  def test_api_url(self):
    conn = Connection('client_token')
    conn.set_api_url('https://api-test.sigopt.com')
    assert conn.impl.api_url == 'https://api-test.sigopt.com'

  def test_api_url_env(self):
    with mock.patch.dict(os.environ, {'SIGOPT_API_URL': 'https://api-env.sigopt.com'}):
      conn = Connection('client_token')
      assert conn.impl.api_url == 'https://api-env.sigopt.com'

  def test_verify(self):
    conn = Connection('client_token')
    conn.set_verify_ssl_certs(False)
    assert conn.impl.requestor.verify_ssl_certs is False

  def test_proxies(self):
    conn = Connection('client_token')
    conn.set_proxies({'http': 'http://127.0.0.1:6543'})
    assert conn.impl.requestor.proxies['http'] == 'http://127.0.0.1:6543'

  def test_error(self):
    with pytest.raises(ValueError):
      Connection()
