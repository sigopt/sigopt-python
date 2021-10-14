import pytest
from mock import Mock

from sigopt.orchestrate.resource.service import ResourceService
from sigopt.orchestrate.template.service import TemplateService


class TestTemplateService(object):
  @pytest.fixture
  def template_service(self):
    services = Mock()
    services.resource_service = ResourceService(services)
    return TemplateService(services)
