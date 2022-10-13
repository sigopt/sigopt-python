# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click
import mock
import pytest
from click.testing import CliRunner

from sigopt.cli import cli


class TestRunCli(object):
  @pytest.mark.parametrize('opt_into_log_collection', [False, True])
  @pytest.mark.parametrize('opt_into_cell_tracking', [False, True])
  def test_config_command(self, opt_into_log_collection, opt_into_cell_tracking):
    runner = CliRunner()
    log_collection_arg = '--enable-log-collection' if opt_into_log_collection else '--no-enable-log-collection'
    cell_tracking_arg = '--enable-cell-tracking' if opt_into_cell_tracking else '--no-enable-cell-tracking'
    with mock.patch('sigopt.cli.commands.config._config.persist_configuration_options') as persist_configuration_options:
      result = runner.invoke(cli, [
        'config',
        '--api-token=some_test_token',
        log_collection_arg,
        cell_tracking_arg,
      ])
      persist_configuration_options.assert_called_once_with({
        'api_token': 'some_test_token',
        'code_tracking_enabled': opt_into_cell_tracking,
        'log_collection_enabled': opt_into_log_collection,
      })
    assert result.exit_code == 0
    assert result.output == ''
