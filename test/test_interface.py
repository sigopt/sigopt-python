import os
import mock
import pytest

from sigopt.config import config
from sigopt.interface import Connection
from sigopt.requestor import DEFAULT_HTTP_TIMEOUT
from sigopt.resource import ApiResource

class TestInterface(object):
  @pytest.yield_fixture
  def config_dict(self, autouse=True):
    with mock.patch.dict(config._configuration, {}):
      yield config._configuration

  def test_create(self):
    conn = Connection(client_token='client_token')
    assert conn.impl.api_url == 'https://api.sigopt.com'
    assert conn.impl.requestor.verify_ssl_certs is None
    assert conn.impl.requestor.session is None
    assert conn.impl.requestor.proxies is None
    assert conn.impl.requestor.timeout == DEFAULT_HTTP_TIMEOUT
    assert conn.impl.requestor.auth.username == 'client_token'
    assert isinstance(conn.clients, ApiResource)
    assert isinstance(conn.experiments, ApiResource)

  def test_create_uses_session_if_provided(self):
    session = mock.Mock()
    conn = Connection(client_token='client_token', session=session)
    assert conn.impl.requestor.session is session

    response = mock.Mock()
    session.request.return_value = response
    response.status_code = 200
    response.text = '{}'
    session.request.assert_not_called()
    conn.experiments().fetch()
    session.request.assert_called_once()

  def test_environment_variable(self):
    with mock.patch.dict(os.environ, {'SIGOPT_API_TOKEN': 'client_token'}):
      conn = Connection()
      assert conn.impl.requestor.auth.username == 'client_token'

  def test_token_in_config(self, config_dict):
    with mock.patch.dict(config_dict, {'api_token': 'test_token_in_config'}), mock.patch.dict(os.environ, {}):
      conn = Connection()
      assert conn.impl.requestor.auth.username == 'test_token_in_config'

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
    with mock.patch.dict(os.environ, {'SIGOPT_API_TOKEN': ''}):
      with pytest.raises(ValueError):
        Connection()

  def test_timeout(self):
    conn = Connection('client_token')
    conn.set_timeout(30)
    assert conn.impl.requestor.timeout == 30
