import pytest
from mock import Mock

from sigopt.orchestrate.ecr.service import AwsEcrService


class TestAwsEcrService(object):
  @pytest.fixture
  def orchestrate_services(self):
    return Mock()

  @pytest.fixture
  def aws_services(self):
    return Mock()

  def test_constructor(self, orchestrate_services, aws_services):
    ecr_service = AwsEcrService(orchestrate_services, aws_services)
    assert ecr_service.client is not None
