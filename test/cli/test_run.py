import click
import mock
import os
import pytest
from click.testing import CliRunner

from sigopt.cli import cli


class TestRunCli(object):
  @pytest.yield_fixture(autouse=True)
  def patch_run_factory(self):
    with mock.patch('sigopt.cli.run.RunFactory'):
      yield

  def test_run_command(self):
    runner = CliRunner()
    result = runner.invoke(cli, [
      'run',
      'test/cli/test_files/print_hello.py',
    ])
    assert result.exit_code == 0
    assert result.output == 'hello\n'

  def test_run_command_with_args(self):
    runner = CliRunner()
    result = runner.invoke(cli, [
      'run',
      'test/cli/test_files/print_args.py',
      '--kwarg=value',
      'positional_arg',
    ])
    assert result.exit_code == 0
    assert result.output == 'test/cli/test_files/print_args.py\n--kwarg=value\npositional_arg\n'

  def test_run_command_import_sibling(self):
    runner = CliRunner()
    result = runner.invoke(cli, [
      'run',
      'test/cli/test_files/import_hello.py',
    ])
    assert result.exit_code == 0
    assert result.output == 'hello\n'

  def test_run_command_ipynb(self):
    runner = CliRunner()
    result = runner.invoke(cli, ['run', 'test/cli/test_files/notebook_hello.ipynb'])
    assert result.exit_code == 0

  def test_run_command_needs_entrypoint(self):
    runner = CliRunner()
    result = runner.invoke(cli, ['run'])
    assert result.exit_code == 2
    assert "Error: Missing argument 'ENTRYPOINT'." in result.output
