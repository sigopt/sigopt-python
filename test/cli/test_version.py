# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from click.testing import CliRunner

from sigopt.cli import cli
from sigopt.version import VERSION


class TestVersionCli(object):
  def test_version_command(self):
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert result.output == VERSION + "\n"
