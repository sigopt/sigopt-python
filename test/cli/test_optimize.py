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
  @pytest.fixture
  def run_context(self):
    run = RunContext(mock.Mock(), mock.Mock(), None)
    run.to_json = mock.Mock(return_value={"run": {}})
    run._end = mock.Mock()
    run._log_source_code = mock.Mock()
    return run

  @pytest.fixture(autouse=True)
  def patch_experiment(self, run_context):
    with mock.patch('sigopt.cli.commands.local.optimize.create_experiment_from_validated_data') as create_experiment:
      experiment = ExperimentContext(mock.Mock(project="test-project"), mock.Mock())
      experiment.create_run = mock.Mock(return_value=run_context)
      experiment.refresh = mock.Mock()
      experiment.is_finished = mock.Mock(side_effect=[False, True])
      create_experiment.return_value = experiment
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

  def test_optimize_command_track_source_code(self, runner, run_context):
    runner.invoke(cli, [
      "optimize",
      "--experiment-file=valid_sigopt.yml",
      "--source-file=print_args.py",
      "python",
      "print_args.py",
    ])
    with open("print_args.py") as fp:
      content = fp.read()
    run_context._log_source_code.assert_called_once_with({"content": content})

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
