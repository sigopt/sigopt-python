import shutil
import click
import mock
import os
import pytest
from click.testing import CliRunner

from sigopt.cli import cli
from sigopt.run_context import RunContext


class TestRunCli(object):
  @pytest.fixture(autouse=True)
  def patch_run_factory(self):
    with mock.patch('sigopt.cli.commands.local.run.SigOptFactory') as factory:
      run = RunContext(mock.Mock(), mock.Mock(), None)
      run.to_json = mock.Mock(return_value={"run": {}})
      run._end = mock.Mock()
      instance = mock.Mock()
      instance.create_run.return_value = run
      factory.from_default_project = mock.Mock(return_value=instance)
      yield

  @pytest.fixture
  def runner(self):
    runner = CliRunner()
    root = os.path.abspath("test/cli/test_files")
    with runner.isolated_filesystem():
      for file in [
        "print_hello.py",
        "print_args.py",
        "import_hello.py",
      ]:
        shutil.copy(os.path.join(root, file), ".")
      yield runner

  def test_run_command_echo(self, runner):
    result = runner.invoke(cli, [
      "run",
      "echo",
      "hello",
    ])
    assert result.exit_code == 0
    assert result.output == "hello\n"

  def test_run_command(self, runner):
    runner = CliRunner()
    result = runner.invoke(cli, [
      "run",
      "python",
      "print_hello.py",
    ])
    assert result.exit_code == 0
    assert result.output == "hello\n"

  def test_run_command_with_args(self, runner):
    result = runner.invoke(cli, [
      "run",
      "python",
      "print_args.py",
      "--kwarg=value",
      "positional_arg",
    ])
    assert result.output == "print_args.py\n--kwarg=value\npositional_arg\n"
    assert result.exit_code == 0

  def test_run_command_import_sibling(self, runner):
    result = runner.invoke(cli, [
      "run",
      "python",
      "import_hello.py",
    ])
    assert result.output == "hello\n"
    assert result.exit_code == 0
