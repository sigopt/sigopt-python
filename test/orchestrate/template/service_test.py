import re

import pytest
import yaml
from mock import Mock

from sigopt.orchestrate.resource.service import ResourceService
from sigopt.orchestrate.template.service import TemplateService


class TestTemplateService(object):
  @pytest.fixture
  def template_service(self):
    services = Mock()
    services.resource_service = ResourceService(services)
    return TemplateService(services)

  def test_config_map(self, template_service):
    role_config_map = template_service.render_yaml_template_from_file('eks/config_map.yml.ms', dict(
      node_instance_role_arn="NODE_ROLE_ARN",
      cluster_access_role_arn="CLUSTER_ROLE_ARN",
      cluster_access_role_name="CLUSTER_ROLE_NAME",
    ))
    assert re.search(r'\s+(- )?rolearn: "NODE_ROLE_ARN"', role_config_map)
    assert re.search(r'\s+(- )?rolearn: "CLUSTER_ROLE_ARN"', role_config_map)
    assert re.search(r'\s+(- )?username: "CLUSTER_ROLE_NAME"', role_config_map)

  def test_dockerfile_escape(self, template_service):
    rendered = template_service.render_dockerfile_template_from_file('model_packer/Dockerfile.ms', dict(
      sigopt_home='\nCOPY .',
    ))
    # Ensure that the newline is preceded by a backslash, so Dockerfile doesn't interpret it as a new command
    assert 'ENV SIGOPT_HOME "\\\nCOPY ."' in rendered

    rendered = template_service.render_dockerfile_template_from_file('model_packer/Dockerfile.ms', dict(
      sigopt_home='echo ""\\',
    ))
    # Ensure that the trailing backslash is escaped, and not interpreted as an escape sequence for the newline
    assert 'ENV SIGOPT_HOME "echo ""\\\\"\n' in rendered

  def test_yaml_escape(self, template_service):
    rendered = template_service.render_yaml_template_from_file('test.yml.ms', dict(
      endpoint_url='"', base64_encoded_ca_cert='\\',
    ))
    parsed = yaml.safe_load(rendered)
    assert parsed['clusters'][0]['cluster']['server'] == '"'
    assert parsed['clusters'][0]['cluster']['certificate-authority-data'] == '\\'
