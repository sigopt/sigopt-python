import pytest
import simplejson

from sigopt.exception import ApiException
from sigopt.interface import Connection
from sigopt.objects import Experiment

class MockResponse(object):
  def __init__(self, json, status_code, text=None):
    self._json = json
    self.status_code = status_code
    self.text = text

  def json(self):
    if self._json is not None:
      return self._json
    else:
      raise simplejson.decoder.JSONDecodeError('', '', 0)


class MockRequestor(object):
  def __init__(self, response):
    self.response = response

  def get(self, *args, **kwargs):
    return self.response

  def post(self, *args, **kwargs):
    return self.response

  def put(self, *args, **kwargs):
    return self.response

  def delete(self, *args, **kwargs):
    return self.response


MESSAGE = 'This is an exception message.'

SAMPLE_EXCEPTION = {
  'message': MESSAGE,
}

SAMPLE_RESPONSE = {
  'number': 1.2,
  'string': 'abc',
  'list': [1,2,3],
  'object': {
    'key': 'value',
  }
}

class TestRequestor(object):
  @pytest.fixture
  def connection(self):
    return Connection('client_token')

  def returns(self, response):
    return MockRequestor(response)

  def test_ok(self, connection):
    connection.requestor = self.returns(MockResponse(SAMPLE_RESPONSE, status_code=200))
    assert connection.experiments(1).fetch() == Experiment(SAMPLE_RESPONSE)
    assert connection.experiments().create() == Experiment(SAMPLE_RESPONSE)
    assert connection.experiments(1).update() == Experiment(SAMPLE_RESPONSE)
    assert connection.experiments(1).delete() == Experiment(SAMPLE_RESPONSE)

  def test_ok_code(self, connection):
    connection.requestor = self.returns(MockResponse(SAMPLE_RESPONSE, status_code=201))
    assert connection.experiments(1).fetch() == Experiment(SAMPLE_RESPONSE)

  def test_response(self, connection):
    connection.requestor = self.returns(MockResponse(SAMPLE_RESPONSE, status_code=200))
    assert connection.experiments(1).fetch() == Experiment(SAMPLE_RESPONSE)

  def test_client_error(self, connection):
    connection.requestor = self.returns(MockResponse(SAMPLE_RESPONSE, status_code=400))
    with pytest.raises(ApiException) as e:
      connection.experiments(1).fetch()
    e = e.value
    assert str(e) == 'ApiException (400): '
    assert e.status_code == 400
    assert e.to_json() == SAMPLE_RESPONSE

  def test_client_error_message(self, connection):
    connection.requestor = self.returns(MockResponse(SAMPLE_EXCEPTION, status_code=400))
    with pytest.raises(ApiException) as e:
      connection.experiments(1).fetch()
    e = e.value
    assert str(e) == 'ApiException (400): ' + MESSAGE
    assert e.status_code == 400
    assert e.to_json() == SAMPLE_EXCEPTION

  def test_server_error(self, connection):
    connection.requestor = self.returns(MockResponse(SAMPLE_EXCEPTION, status_code=500))
    with pytest.raises(ApiException) as e:
      connection.experiments(1).fetch()
    e = e.value
    assert str(e) == 'ApiException (500): ' + MESSAGE
    assert e.status_code == 500
    assert e.to_json() == SAMPLE_EXCEPTION

  def test_malformed_client_error(self, connection):
    connection.requestor = self.returns(MockResponse(None, status_code=404, text=MESSAGE))
    with pytest.raises(ApiException) as e:
      connection.experiments(1).fetch()
    e = e.value
    assert str(e) == 'ApiException (404): ' + MESSAGE
    assert e.status_code == 404
    assert e.to_json() == SAMPLE_EXCEPTION

  def test_malformed_server_error(self, connection):
    connection.requestor = self.returns(MockResponse(None, status_code=500, text=MESSAGE))
    with pytest.raises(ApiException) as e:
      connection.experiments(1).fetch()
    e = e.value
    assert str(e) == 'ApiException (500): ' + MESSAGE
    assert e.status_code == 500
    assert e.to_json() == SAMPLE_EXCEPTION
