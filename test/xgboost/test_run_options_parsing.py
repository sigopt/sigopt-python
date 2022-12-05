# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from mock import Mock
import pytest
import random

from sigopt.objects import TrainingRun
from sigopt.run_context import RunContext
from sigopt.xgboost.run import DEFAULT_RUN_OPTIONS, parse_run_options, XGBRunHandler
from ..utils import ObserveWarnings

class TestXGBoostKwargs(object):
  def test_xgboost_kwargs_remove_wrong_key(self):
    kwargs = {
      "WRONG_KEY_1": True,
      "WRONG_KEY_2": 3.14,
    }
    with ObserveWarnings() as ws:
      xgb_run_handler = XGBRunHandler(
        params={"max_depth": 2},
        dtrain=Mock(),
        num_boost_round=21,
        evals=None,
        early_stopping_rounds=10,
        evals_result=None,
        verbose_eval=True,
        xgb_model=Mock(),
        callbacks=None,
        run_options=None,
        **kwargs
      )
      assert not xgb_run_handler.kwargs
      assert len(ws) == len(kwargs)
      for w in ws:
        assert issubclass(w.category, RuntimeWarning)

  def test_xgboost_kwargs_keep_right_key(self):
    xgb_run_handler = XGBRunHandler(
      params={"max_depth": 2},
      dtrain=Mock(),
      num_boost_round=21,
      evals=None,
      early_stopping_rounds=None,
      evals_result=None,
      verbose_eval=True,
      xgb_model=None,
      callbacks=None,
      maximize=True,
      run_options={"autolog_metrics": True},
    )
    assert len(xgb_run_handler.kwargs) == 1
    assert "maximize" in xgb_run_handler.kwargs
    assert xgb_run_handler.kwargs["maximize"] == True

class TestRunOptionsParsing(object):
  def test_run_options_wrong_type(self):
    run_options = Mock(log_params=True)
    with pytest.raises(TypeError):
      parse_run_options(run_options)

  def test_run_options_wrong_keys(self):
    run_options = {
      'autolog_metric': True,
    }
    with pytest.raises(ValueError):
      parse_run_options(run_options)

  def test_run_options_autolog_not_bool(self):
    run_options = {
      'autolog_metrics': 12,
    }
    with pytest.raises(TypeError):
      parse_run_options(run_options)

  def test_run_options_run_and_name_keys(self):
    run_options = {
      'name': 'test-run',
      'run': Mock(),
    }
    with pytest.raises(ValueError):
      parse_run_options(run_options)

    run_options = {
      'name': None,
      'run': None,
    }
    assert parse_run_options(run_options)

    run_options = {
      'name': "",
      'run': None,
    }
    assert parse_run_options(run_options)

    run_options = {
      'name': "",
      'run': RunContext(Mock(), Mock(assignments={'a': 1})),
    }
    assert parse_run_options(run_options)

  def test_run_options_run_context_object(self):
    run_options = {
      'run': TrainingRun(Mock())
    }
    with pytest.raises(TypeError):
      parse_run_options(run_options)

    run_options = {
      'run': RunContext(Mock(), Mock(assignments={'a': 1})),
    }
    assert parse_run_options(run_options)

  def test_run_options_fully_parsed(self):
    num_of_options = random.randint(1, len(DEFAULT_RUN_OPTIONS))
    run_options_keys = random.sample(DEFAULT_RUN_OPTIONS.keys(), num_of_options)
    run_options = {k: DEFAULT_RUN_OPTIONS[k] for k in run_options_keys}
    parsed_options = parse_run_options(run_options)
    assert set(parsed_options.keys()) == set(DEFAULT_RUN_OPTIONS.keys())
