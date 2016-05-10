# -*- coding: utf-8 -*-

import pytest

from sigopt.compat import json
from sigopt.exception import ApiException, ConnectionException
from sigopt.interface import ConnectionImpl
from sigopt.objects import Experiment
import sigopt.vendored.six as six

class MockRequestor(object):
  def __init__(self, response):
    self.response = response

  def __getattr__(self, name):
    def func(*args, **kwargs):
      if isinstance(self.response, Exception):
        raise self.response
      return self.response
    func.__name__ = name
    return func


MESSAGE = 'This is an exception message.'
UNICODE_MESSAGE = six.u('This is a friendly 👬 message')
UNICODE_STR_MESSAGE = UNICODE_MESSAGE.encode('utf-8')

SAMPLE_EXCEPTION = {
  'message': MESSAGE,
}

SAMPLE_UNICODE_EXCEPTION = {
  'message': UNICODE_MESSAGE,
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
  def returns(self, response):
    return MockRequestor(response)

  def test_ok(self):
    connection = ConnectionImpl(self.returns(SAMPLE_RESPONSE))
    assert connection.experiments(1).fetch() == Experiment(SAMPLE_RESPONSE)
    assert connection.experiments().create() == Experiment(SAMPLE_RESPONSE)
    assert connection.experiments(1).update() == Experiment(SAMPLE_RESPONSE)
    assert connection.experiments(1).delete() == Experiment(SAMPLE_RESPONSE)

  def test_ok_code(self):
    connection = ConnectionImpl(self.returns(SAMPLE_RESPONSE))
    assert connection.experiments(1).fetch() == Experiment(SAMPLE_RESPONSE)

  def test_response(self):
    connection = ConnectionImpl(self.returns(SAMPLE_RESPONSE))
    assert connection.experiments(1).fetch() == Experiment(SAMPLE_RESPONSE)

  def test_client_error(self):
    connection = ConnectionImpl(self.returns(ApiException(SAMPLE_RESPONSE, 400)))
    with pytest.raises(ApiException) as e:
      connection.experiments(1).fetch()
    e = e.value
    assert str(e) == 'ApiException (400): '
    assert e.status_code == 400
    assert e.to_json() == SAMPLE_RESPONSE

  def test_client_error_message(self):
    connection = ConnectionImpl(self.returns(ApiException(SAMPLE_EXCEPTION, 400)))
    with pytest.raises(ApiException) as e:
      connection.experiments(1).fetch()
    e = e.value
    assert str(e) == 'ApiException (400): ' + MESSAGE
    assert e.status_code == 400
    assert e.to_json() == SAMPLE_EXCEPTION

  def test_server_error(self):
    connection = ConnectionImpl(self.returns(ApiException(SAMPLE_EXCEPTION, status_code=500)))
    with pytest.raises(ApiException) as e:
      connection.experiments(1).fetch()
    e = e.value
    assert str(e) == 'ApiException (500): ' + MESSAGE
    assert e.status_code == 500
    assert e.to_json() == SAMPLE_EXCEPTION

  def test_connection_error(self):
    connection = ConnectionImpl(self.returns(ConnectionException('fake connection exception')))
    with pytest.raises(ConnectionException) as e:
      connection.experiments(1).fetch()
    e = e.value
    assert str(e) == 'ConnectionException: fake connection exception'

  def test_unicode_json(self):
    connection = ConnectionImpl(self.returns(ApiException(SAMPLE_UNICODE_EXCEPTION, 500)))
    with pytest.raises(ApiException) as e:
      connection.experiments(1).fetch()
    e = e.value
    if six.PY2:
      assert unicode(e) == six.u('ApiException (500): ') + UNICODE_MESSAGE
      assert str(e) == 'ApiException (500): ' + UNICODE_STR_MESSAGE
    else:
      assert str(e) == 'ApiException (500): ' + UNICODE_MESSAGE
