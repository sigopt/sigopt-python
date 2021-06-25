import pytest
from mock import Mock

from sigopt.orchestrate.sts.service import AwsStsService


class TestAwsStsService(object):
  @pytest.fixture
  def orchestrate_services(self):
    return Mock()

  @pytest.fixture
  def aws_services(self):
    return Mock()

  def test_constructor(self, orchestrate_services, aws_services):
    sts_service = AwsStsService(orchestrate_services, aws_services)
    assert sts_service.client is not None
