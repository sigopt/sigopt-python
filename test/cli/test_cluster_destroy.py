# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from click.testing import CliRunner
from mock import Mock, patch

from sigopt.cli import cli


class TestClusterDestroyCli(object):
  def test_cluster_destroy_command(self):
    services = Mock()
    cluster = Mock()
    cluster.name = "foobar"
    cluster.provider_string = "aws"
    services.cluster_service.get_connected_cluster.return_value = cluster
    runner = CliRunner()
    with patch("sigopt.orchestrate.controller.OrchestrateServiceBag", return_value=services):
      result = runner.invoke(cli, ["cluster", "destroy"])
    services.kubernetes_service.cleanup_for_destroy.assert_called_once()
    services.cluster_service.destroy.assert_called_once_with(
      cluster_name="foobar",
      provider_string="aws",
    )
    assert result.output.splitlines() == [
      "Destroying cluster foobar, this process may take 20-30 minutes or longer...",
      "Successfully destroyed kubernetes cluster: foobar",
    ]
    assert result.exit_code == 0
