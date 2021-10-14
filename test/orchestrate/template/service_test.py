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

  def test_dockerfile_escape_newline(self, template_service):
    rendered = template_service.render_dockerfile_template_from_file('model_packer/Dockerfile.ms', dict(
      sigopt_home='\nCOPY .',
    ))
    # Ensure that the newline is preceded by a backslash, so Dockerfile doesn't interpret it as a new command
    assert 'ENV SIGOPT_HOME "\\\nCOPY ."' in rendered

  @pytest.mark.skip(reason="chevron doesn't handle quotes gracefully")
  def test_dockerfile_escape_backslash(self, template_service):
    rendered = template_service.render_dockerfile_template_from_file('model_packer/Dockerfile.ms', dict(
      sigopt_home='echo ""\\',
    ))
    # Ensure that the trailing backslash is escaped, and not interpreted as an escape sequence for the newline
    assert 'ENV SIGOPT_HOME "echo ""\\\\"\n' in rendered
