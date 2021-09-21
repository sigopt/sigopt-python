import click
import mock
import pytest
from click.testing import CliRunner
from mock import Mock, patch

from sigopt.cli import cli


class TestRunCli(object):
  def test_orchestrate_run(self):
    services = Mock()
    runner = CliRunner()
    with runner.isolated_filesystem():
      with \
        patch('sigopt.orchestrate.controller.OrchestrateServiceBag', return_value=services), \
        patch('sigopt.orchestrate.docker.service.DockerService.create'), \
        patch(
          'sigopt.orchestrate.docker.service.DockerService.get_repository_and_tag',
          return_value=("docker.io/test", "123"),
        ):
        services.cluster_service.assert_is_connected = Mock()
        services.gpu_options_validator_service.get_resource_options = Mock(return_value=None)
        open("Dockerfile", "w").close()
        result = runner.invoke(cli, ["cluster", "run", "echo", "hello"])
      assert result.exit_code == 0
