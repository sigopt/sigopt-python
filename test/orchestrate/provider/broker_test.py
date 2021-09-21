import pytest
from mock import Mock

from sigopt.orchestrate.aws.service import AwsService
from sigopt.orchestrate.custom_cluster.service import CustomClusterService
from sigopt.orchestrate.provider.broker import ProviderBroker
from sigopt.orchestrate.provider.constants import Provider, string_to_provider


class TestProviderBroker(object):
  @pytest.fixture
  def services(self):
    return Mock(
      get_option=Mock(return_value='foo'),
    )

  @pytest.fixture
  def provider_broker(self, services):
    return ProviderBroker(services)

  def test_get_provider_service(self, provider_broker, services):
    assert isinstance(provider_broker.get_provider_service(string_to_provider('aws')), AwsService)
    assert isinstance(provider_broker.get_provider_service(string_to_provider('AWS')), AwsService)
    assert isinstance(provider_broker.get_provider_service(Provider.AWS), AwsService)

  def test_custom_provider(self, provider_broker, services):
    assert isinstance(provider_broker.get_provider_service(string_to_provider('custom')), CustomClusterService)
    assert isinstance(provider_broker.get_provider_service(Provider.CUSTOM), CustomClusterService)

  def test_unknown_provider(self, provider_broker):
    with pytest.raises(NotImplementedError):
      provider_broker.get_provider_service(0)
