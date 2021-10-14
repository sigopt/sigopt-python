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

  @pytest.mark.skip(reason="chevron doesn't handle quotes gracefully")
  def test_yaml_escape_quotes(self, template_service):
    rendered = template_service.render_yaml_template_from_file('test.yml.ms', dict(
      endpoint_url='"', base64_encoded_ca_cert='"',
    ))
    parsed = yaml.safe_load(rendered)
    assert parsed['clusters'][0]['cluster']['server'] == '"'
    assert parsed['clusters'][0]['cluster']['certificate-authority-data'] == '"'

  def test_yaml_escape_backslash(self, template_service):
    rendered = template_service.render_yaml_template_from_file('test.yml.ms', dict(
      endpoint_url='\\', base64_encoded_ca_cert='\\',
    ))
    parsed = yaml.safe_load(rendered)
    assert parsed['clusters'][0]['cluster']['server'] == '\\'
    assert parsed['clusters'][0]['cluster']['certificate-authority-data'] == '\\'
