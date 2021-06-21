import click
import mock
import os
import pytest
from click.testing import CliRunner

from sigopt.cli import cli
from sigopt.experiment_context import ExperimentContext
from sigopt.run_context import RunContext


class TestRunCli(object):
  @pytest.fixture(autouse=True)
  def patch_factory(self):
    with mock.patch('sigopt.cli.optimize.SigOptFactory') as factory:
      run = RunContext(mock.Mock(), mock.Mock(), None)
      run.to_json = mock.Mock(return_value={"run": {}})
      run._end = mock.Mock()
      experiment = ExperimentContext(mock.Mock(project="test-project"))
      experiment.create_run = mock.Mock(return_value=run)
      experiment.refresh = mock.Mock()
      experiment.is_finished = mock.Mock(side_effect=[False, True])
      instance = mock.Mock()
      instance.create_experiment.return_value = experiment
      factory.return_value = instance
      yield

  def test_optimize_command(self):
    runner = CliRunner()
    result = runner.invoke(cli, [
      'optimize',
      '--sigopt-file=test/cli/test_files/valid_sigopt.yml',
      'test/cli/test_files/print_hello.py',
    ])
    assert result.exit_code == 0
    assert result.output == 'hello\n'

  def test_optimize_command_with_args(self):
    runner = CliRunner()
    result = runner.invoke(cli, [
      'optimize',
      '--sigopt-file=test/cli/test_files/valid_sigopt.yml',
      'test/cli/test_files/print_args.py',
      '--kwarg=value',
      'positional_arg',
    ])
    assert result.exit_code == 0
    assert result.output == 'test/cli/test_files/print_args.py\n--kwarg=value\npositional_arg\n'

  def test_optimize_ipynb(self):
    runner = CliRunner()
    result = runner.invoke(cli, [
      'optimize',
      '--sigopt-file=test/cli/test_files/valid_sigopt.yml',
      'test/cli/test_files/notebook_hello.ipynb',
    ])
    assert result.exit_code == 0

  def test_optimize_command_needs_entrypoint(self):
    runner = CliRunner()
    result = runner.invoke(cli, ['optimize'])
    assert result.exit_code == 2
    assert "Error: Missing argument 'ENTRYPOINT'." in result.output

  @pytest.fixture
  def no_top_level_sigopt_yaml(self):
    if os.path.isfile('./sigopt.yml'):
      raise Exception('The sigopt.yml file cannot exist at the top level of sigopt-python when running tests')

  def test_optimize_command_needs_existing_entrypoint(self, no_top_level_sigopt_yaml):
    runner = CliRunner()
    result = runner.invoke(cli, ['optimize', 'test/cli/test_files/does_not_exist.py'])
    assert result.exit_code == 1
    assert "Provided entrypoint 'test/cli/test_files/does_not_exist.py' does not exist" in str(result.exception)

  def test_optimize_command_needs_existing_sigopt_yaml(self, no_top_level_sigopt_yaml):
    runner = CliRunner()
    result = runner.invoke(cli, ['optimize', 'test/cli/test_files/print_hello.py'])
    assert result.exit_code == 1
    assert "The sigopt file 'sigopt.yml' is missing" in str(result.exception)

  @pytest.mark.xfail(reason='Warnings not appearing in stderr')
  def test_warning_from_sigopt_yaml(self, no_top_level_sigopt_yaml):
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(cli, [
      'optimize',
      '--sigopt-file=test/cli/test_files/warning_sigopt.yml',
      'test/cli/test_files/print_hello.py',
    ])
    assert result.exit_code == 0
    assert 'The following keys' in str(result.stderr)

  def test_optimize_command_needs_valid_sigopt_yaml(self, no_top_level_sigopt_yaml):
    runner = CliRunner()
    result = runner.invoke(cli, [
      'optimize',
      '--sigopt-file=test/cli/test_files/invalid_sigopt.yml',
      'test/cli/test_files/print_hello.py',
    ])
    assert result.exit_code == 1
    assert 'must be a mapping' in str(result.exception)
