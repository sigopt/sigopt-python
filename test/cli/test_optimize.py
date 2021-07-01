import click
import mock
import os
import pytest
import shutil
from click.testing import CliRunner

from sigopt.cli import cli
from sigopt.experiment_context import ExperimentContext
from sigopt.run_context import RunContext


class TestRunCli(object):
  @pytest.fixture(autouse=True)
  def patch_factory(self):
    with mock.patch('sigopt.cli.commands.local.optimize.SigOptFactory') as factory:
      run = RunContext(mock.Mock(), mock.Mock(), None)
      run.to_json = mock.Mock(return_value={"run": {}})
      run._end = mock.Mock()
      experiment = ExperimentContext(mock.Mock(project="test-project"), mock.Mock())
      experiment.create_run = mock.Mock(return_value=run)
      experiment.refresh = mock.Mock()
      experiment.is_finished = mock.Mock(side_effect=[False, True])
      instance = mock.Mock()
      instance.create_prevalidated_experiment.return_value = experiment
      factory.return_value = instance
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
        "valid_sigopt.yml",
        "invalid_sigopt.yml",
      ]:
        shutil.copy(os.path.join(root, file), ".")
      yield runner

  def test_optimize_command(self, runner):
    result = runner.invoke(cli, [
      "optimize",
      "--experiment-file=valid_sigopt.yml",
      "python",
      "print_hello.py",
    ])
    assert result.output == "hello\n"
    assert result.exit_code == 0

  def test_optimize_command_with_args(self, runner):
    result = runner.invoke(cli, [
      "optimize",
      "--experiment-file=valid_sigopt.yml",
      "python",
      "print_args.py",
      "--kwarg=value",
      "positional_arg",
      "--",
      "after -- arg",
    ])
    assert result.output == "print_args.py\n--kwarg=value\npositional_arg\n--\nafter -- arg\n"
    assert result.exit_code == 0

  def test_optimize_command_needs_existing_sigopt_yaml(self, runner):
    runner = CliRunner()
    result = runner.invoke(cli, ["optimize", "python", "print_hello.py"])
    assert "Path 'experiment.yml' does not exist" in result.output
    assert result.exit_code == 2

  def test_optimize_command_needs_valid_sigopt_yaml(self, runner):
    runner = CliRunner()
    result = runner.invoke(cli, [
      "optimize",
      "--experiment-file=invalid_sigopt.yml",
      "python",
      "print_hello.py",
    ])
    assert "The top level should be a mapping of keys to values" in str(result.output)
    assert result.exit_code == 2
