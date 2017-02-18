import mock
import pytest

from sigopt.endpoint import BoundApiEndpoint
from sigopt.interface import ConnectionImpl
from sigopt.resource import BoundApiResource, PartiallyBoundApiResource

class TestResource(object):
  @pytest.fixture
  def connection(self):
    return ConnectionImpl(requestor=None)

  def test_partial_bind_resource(self, connection):
    assert isinstance(connection.experiments().observations, PartiallyBoundApiResource)
    assert isinstance(connection.experiments(1).observations, PartiallyBoundApiResource)
    assert isinstance(connection.experiments().observations, PartiallyBoundApiResource)
    assert isinstance(connection.experiments(1).observations, PartiallyBoundApiResource)

  def test_bind_resource(self, connection):
    api_resource = connection.experiments
    assert isinstance(api_resource(), BoundApiResource)
    assert isinstance(api_resource(1), BoundApiResource)

    partially_bound_api_resource = connection.experiments().observations
    assert isinstance(partially_bound_api_resource(), BoundApiResource)
    assert isinstance(partially_bound_api_resource(1), BoundApiResource)

  def test_bind_endpoint(self, connection):
    assert isinstance(connection.experiments().fetch, BoundApiEndpoint)
    assert isinstance(connection.experiments(1).fetch, BoundApiEndpoint)

  def test_get_bound_entity(self, connection):
    assert isinstance(connection.experiments().get_bound_entity('fetch'), BoundApiEndpoint)
    assert isinstance(connection.experiments().get_bound_entity('observations'), PartiallyBoundApiResource)
