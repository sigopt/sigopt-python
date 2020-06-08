import numpy
import pytest
import warnings

from sigopt.lib import *
from sigopt.vendored import six as _six

LONG_NUMBER = 100000000000000000000000

class TestBase(object):
  @pytest.fixture(autouse=True)
  def set_warnings(self):
    warnings.simplefilter("error")

  def test_is_integer(self):
    assert is_integer(int('3')) is True
    assert is_integer(0) is True
    assert is_integer(LONG_NUMBER) is True
    assert is_integer(numpy.int32()) is True
    assert is_integer(numpy.int64()) is True

    assert is_integer([]) is False
    assert is_integer([2]) is False
    assert is_integer({1: 2}) is False
    assert is_integer(None) is False
    assert is_integer(True) is False
    assert is_integer(False) is False
    assert is_integer(4.0) is False
    assert is_integer('3') is False
    assert is_integer(3.14) is False
    assert is_integer(numpy.float32()) is False
    assert is_integer(numpy.float64()) is False
    assert is_integer(numpy.nan) is False

  def test_is_number(self):
    assert is_number(int('3')) is True
    assert is_number(0) is True
    assert is_number(LONG_NUMBER) is True
    assert is_number(4.0) is True
    assert is_number(3.14) is True
    assert is_number(numpy.int32()) is True
    assert is_number(numpy.int64()) is True
    assert is_number(numpy.float32()) is True
    assert is_number(numpy.float64()) is True

    assert is_number([]) is False
    assert is_number([2]) is False
    assert is_number({1: 2}) is False
    assert is_number(None) is False
    assert is_number(True) is False
    assert is_number(False) is False
    assert is_number('3') is False
    assert is_number(numpy.nan) is False

  def test_is_numpy_array(self):
    assert is_numpy_array(numpy.array([]))
    assert is_numpy_array(numpy.array([1, 2, 3]))

    assert not is_numpy_array([])
    assert not is_numpy_array([1, 2, 3])
    assert not is_numpy_array(())
    assert not is_numpy_array((1, 2, 3))
    assert not is_numpy_array(None)
    assert not is_numpy_array(False)
    assert not is_numpy_array(True)
    assert not is_numpy_array(0)
    assert not is_numpy_array(1.0)
    assert not is_numpy_array('abc')
    assert not is_numpy_array(u'abc')
    assert not is_numpy_array(b'abc')
    assert not is_numpy_array({})
    assert not is_numpy_array({'a': 123})
    assert not is_numpy_array(set())
    assert not is_numpy_array(set((1, 'a')))
    assert not is_numpy_array({1, 'a'})
    assert not is_numpy_array(frozenset((1, 'a')))

  def test_is_sequence(self):
    assert is_sequence([])
    assert is_sequence([1, 2, 3])
    assert is_sequence(())
    assert is_sequence((1, 2, 3))
    assert is_sequence(numpy.array([]))
    assert is_sequence(numpy.array([1, 2, 3]))

    assert not is_sequence(None)
    assert not is_sequence(False)
    assert not is_sequence(True)
    assert not is_sequence(0)
    assert not is_sequence(1.0)
    assert not is_sequence('abc')
    assert not is_sequence(u'abc')
    assert not is_sequence(b'abc')
    assert not is_sequence({})
    assert not is_sequence({'a': 123})
    assert not is_sequence(set())
    assert not is_sequence(set((1, 'a')))
    assert not is_sequence({1, 'a'})
    assert not is_sequence(frozenset((1, 'a')))

  def test_is_mapping(self):
    assert is_mapping({})
    assert is_mapping({'a': 123})

    assert not is_mapping([])
    assert not is_mapping([1, 2, 3])
    assert not is_mapping(())
    assert not is_mapping((1, 2, 3))
    assert not is_mapping(numpy.array([]))
    assert not is_mapping(numpy.array([1, 2, 3]))
    assert not is_mapping(None)
    assert not is_mapping(False)
    assert not is_mapping(True)
    assert not is_mapping(0)
    assert not is_mapping(1.0)
    assert not is_mapping('abc')
    assert not is_mapping(u'abc')
    assert not is_mapping(b'abc')
    assert not is_mapping(set())
    assert not is_mapping(set((1, 'a')))
    assert not is_mapping({1, 'a'})
    assert not is_mapping(frozenset((1, 'a')))

  def test_is_string(self):
    assert is_string('abc')
    assert is_string(u'abc')

    if not isinstance('abc', _six.binary_type):
        assert not is_string(b'abc')

    assert not is_string({})
    assert not is_string({'a': 123})
    assert not is_string([])
    assert not is_string([1, 2, 3])
    assert not is_string(())
    assert not is_string((1, 2, 3))
    assert not is_string(numpy.array([]))
    assert not is_string(numpy.array([1, 2, 3]))
    assert not is_string(None)
    assert not is_string(False)
    assert not is_string(True)
    assert not is_string(0)
    assert not is_string(1.0)
    assert not is_string(set())
    assert not is_string(set((1, 'a')))
    assert not is_string({1, 'a'})
    assert not is_string(frozenset((1, 'a')))
