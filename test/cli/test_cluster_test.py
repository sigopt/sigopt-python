from click.testing import CliRunner
from mock import Mock, patch

from sigopt.cli import cli


class TestClusterTestCli(object):
  def test_cluster_test_command(self):
    services = Mock()
    runner = CliRunner()
    with \
      patch('sigopt.orchestrate.controller.OrchestrateServiceBag', return_value=services), \
      patch('sigopt.orchestrate.controller.DockerService'):
      result = runner.invoke(cli, ["cluster", "test"])
    assert result.exit_code == 0
