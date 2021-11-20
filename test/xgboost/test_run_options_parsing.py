from mock import Mock
import pytest
import random

from sigopt.run_context import RunContext
from sigopt.xgboost.run import (
  DEFAULT_RUN_OPTIONS,
  parse_run_options,
)

class TestRunOptionsParsing(object):
  def test_run_options_wrong_keys(self):
    run_options = {
      'log_metric': True,
      'log_params': True,
    }
    with pytest.raises(AssertionError):
      parse_run_options(run_options)

  def test_run_options_conflict_run_name(self):
    run_options = {
      'name': 'test-run',
      'run': Mock(),
    }
    with pytest.raises(AssertionError):
      parse_run_options(run_options)

  def test_run_options_wrong_run_object(self):
    run_options = {
      'run': RunContext(Mock(), Mock(assignments={'a': 1}))
    }
    with pytest.raises(AssertionError):
      parse_run_options(run_options)

  def test_run_options_fully_parsed(self):
    num_of_options = random.randint(1, len(DEFAULT_RUN_OPTIONS))
    run_options_keys = random.sample(DEFAULT_RUN_OPTIONS.keys(), num_of_options)
    run_options = {k: DEFAULT_RUN_OPTIONS[k] for k in run_options_keys}
    parsed_options = parse_run_options(run_options)
    assert set(parsed_options.keys()) == set(DEFAULT_RUN_OPTIONS.keys())
