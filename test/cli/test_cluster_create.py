# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from click.testing import CliRunner
from mock import Mock, patch

from sigopt.cli import cli


class TestClusterCreateCli(object):
  def test_cluster_create(self):
    services = Mock()
    runner = CliRunner()
    with runner.isolated_filesystem(), patch(
      "sigopt.orchestrate.controller.OrchestrateServiceBag", return_value=services
    ):
      open("cluster.yml", "w").close()
      result = runner.invoke(cli, ["cluster", "create"])
    assert result.exit_code == 0
