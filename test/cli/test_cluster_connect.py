# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from click.testing import CliRunner
from mock import Mock, patch

from sigopt.cli import cli


class TestClusterConnectCli(object):
  def test_cluster_connect_command(self):
    services = Mock()
    runner = CliRunner()
    with patch("sigopt.orchestrate.controller.OrchestrateServiceBag", return_value=services):
      result = runner.invoke(cli, ["cluster", "connect", "-n", "foobar", "--provider", "custom"])
    assert result.exit_code == 0
