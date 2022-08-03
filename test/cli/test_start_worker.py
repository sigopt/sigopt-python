import click
import mock
import os
import pytest
import shutil
from click.testing import CliRunner

from sigopt.cli import cli
from sigopt.aiexperiment_context import AIExperimentContext
from sigopt.run_context import RunContext


class TestRunCli(object):
  @pytest.fixture
  def run_context(self):
    run = RunContext(mock.Mock(), mock.Mock(assignments={"fixed1": 0, "fixed2": "test"}))
    run.to_json = mock.Mock(return_value={"run": {}})
    run._end = mock.Mock()
    run._log_source_code = mock.Mock()
    return run

  @pytest.fixture(autouse=True)
  def patch_run_factory(self, run_context):
    with mock.patch('sigopt.cli.commands.local.start_worker.SigOptFactory') as factory:
      experiment = AIExperimentContext(mock.Mock(project="test-project"), mock.Mock())
      experiment.create_run = mock.Mock(return_value=run_context)
      experiment.refresh = mock.Mock()
      experiment.is_finished = mock.Mock(side_effect=[False, True])
      instance = mock.Mock()
      instance.get_experiment.return_value = experiment
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

  def test_start_worker_command(self, runner):
    result = runner.invoke(cli, [
      "start-worker",
      "1234",
      "python",
      "print_hello.py",
    ])
    assert result.output == "hello\n"
    assert result.exit_code == 0

  def test_start_worker_command_with_args(self, runner):
    result = runner.invoke(cli, [
      "start-worker",
      "1234",
      "python",
      "print_args.py",
      "--kwarg=value",
      "positional_arg",
      "--",
      "after -- arg",
    ])
    assert result.output == "print_args.py\n--kwarg=value\npositional_arg\n--\nafter -- arg\n"
    assert result.exit_code == 0

  def test_start_worker_command_track_source_code(self, runner, run_context):
    runner.invoke(cli, [
      "start-worker",
      "--source-file=print_args.py",
      "1234",
      "python",
      "print_args.py",
    ])
    with open("print_args.py") as fp:
      content = fp.read()
    run_context._log_source_code.assert_called_once_with({"content": content})
