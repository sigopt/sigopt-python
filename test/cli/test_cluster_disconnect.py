from click.testing import CliRunner
from mock import Mock, patch

from sigopt.cli import cli


class TestClusterDisconnectCli(object):
  def test_cluster_disconnect_command(self):
    services = Mock()
    runner = CliRunner()
    with patch('sigopt.orchestrate.controller.OrchestrateServiceBag', return_value=services):
      result = runner.invoke(cli, ["cluster", "disconnect"])
    assert result.exit_code == 0
