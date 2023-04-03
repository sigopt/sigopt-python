# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import os

from click.testing import CliRunner

from sigopt.cli import cli


class TestRunCli(object):
  def test_init_command_empty_dir(self):
    files = [
      "run.yml",
      "experiment.yml",
      "Dockerfile",
      ".dockerignore",
    ]
    runner = CliRunner()
    with runner.isolated_filesystem():
      result = runner.invoke(cli, ["init"])
      for filename in files:
        assert os.path.exists(filename)
    assert result.exit_code == 0
    lines = result.output.splitlines()
    assert len(lines) == len(files)
    for line, filename in zip(lines, files):
      assert line == f"Wrote file contents for {filename}"
