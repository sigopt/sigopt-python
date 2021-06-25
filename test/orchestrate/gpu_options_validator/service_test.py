import pytest
from mock import Mock

from sigopt.orchestrate.gpu_options_validator.service import RESOURCES_OPTION, GpuOptionsValidatorService


class TestOptionsValidatorService(object):
  @pytest.fixture()
  def gpu_options_validator_service(self):
    services = Mock()
    return GpuOptionsValidatorService(services)

  @pytest.mark.parametrize(
    'input_gpus,expected_resources',
    [
      (None, {}),
      (0, {'gpus': 0}),
    ],
  )
  def test_get_resources_without_confirmation(
    self,
    gpu_options_validator_service,
    input_gpus,
    expected_resources,
  ):
    options = {}
    if input_gpus is not None:
      options[RESOURCES_OPTION] = {'gpus': input_gpus}
    resource_options = gpu_options_validator_service.get_resource_options(options)
    assert resource_options == expected_resources

  def test_get_local_without_gpus(self, gpu_options_validator_service):
    options = {}
    resource_options = gpu_options_validator_service.get_resource_options(options)
    assert RESOURCES_OPTION not in resource_options
