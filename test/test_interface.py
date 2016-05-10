import os
import pytest

from sigopt.interface import Connection
from sigopt.resource import ApiResource

class TestInterface(object):
  def test_create(self):
    conn = Connection(client_token='client_token')
    conn.set_api_url('https://api-test.sigopt.com')
    assert isinstance(conn.clients, ApiResource)
    assert isinstance(conn.experiments, ApiResource)

  def test_environment_variable(self):
    os.environ['SIGOPT_API_TOKEN'] = 'client_token'
    Connection()
    del os.environ['SIGOPT_API_TOKEN']

  def test_error(self):
    with pytest.raises(ValueError):
      Connection()

