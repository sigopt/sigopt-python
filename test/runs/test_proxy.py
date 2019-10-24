import mock
import pytest

from sigopt.runs.proxy import ProxyMethod


class TestProxyMethod(object):
  @pytest.fixture
  def wrapped_instance(self):
    return mock.Mock()

  @pytest.fixture
  def proxy_method_object(self, wrapped_instance):

    class ProxyMethodTestClass(ProxyMethod):
      instance = wrapped_instance

    return ProxyMethodTestClass('test_method')

  def test_method_call(self, wrapped_instance, proxy_method_object):
    proxy_method_object('test arg', test_kwarg='test')
    wrapped_instance.test_method.assert_called_once_with('test arg', test_kwarg='test')

  def test_docstr(self, wrapped_instance, proxy_method_object):
    wrapped_instance.test_method.__doc__ = 'test docstring'
    assert proxy_method_object.__doc__ == wrapped_instance.test_method.__doc__
