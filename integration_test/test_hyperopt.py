# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from hyperopt import fmin, tpe, hp, STATUS_OK, STATUS_FAIL, SparkTrials
from hyperopt.mongoexp import MongoTrials
import hyperopt
from sigopt.hyperopt import SigOptTrials, upload_trials
import sigopt
import numpy as np
import pytest
import time
import uuid

def objective(p, threshold=1.0, max_sleep_time=0.0):
  x, y = p['x'], p['y']
  if max_sleep_time > 0:
    time.sleep(np.random.rand() * max_sleep_time)
  w = np.random.rand()
  if w <= threshold:
    return {
      'loss': x ** 2 + y ** 2,
      'sum': x + y,
      'status': STATUS_OK
    }
  else:
    return {
      'status': STATUS_FAIL
    }

def objective_random(x):
  return objective(x, 0.8)

def objective_success(x):
  return objective(x, 1.0)

def objective_fail(x):
  return objective(x, -1.0)

class TestHyperopt(object):
  def run_fmin(self, online=True, upload=True, objective=objective_success, max_evals=3, wrap=None, **kwargs):
    project = 'hyperopt-integration-test'
    if wrap == 'mongo':
      trials = MongoTrials('mongo://mongodb:27017/foo_db/jobs', exp_key=str(uuid.uuid4()))
    elif wrap == 'spark':
      trials = SparkTrials()
    else:
      trials = None
    trials = SigOptTrials(project=project, online=(online and upload), trials=trials)
    try:
      best = fmin(objective,
                  space={
                    'x' : hp.uniform('x', -10, 10),
                    'y': hp.uniform('y', -10, 10)
                  },
                  algo=tpe.suggest,
                  max_evals=max_evals,
                  trials=trials,
                  **kwargs
                  )
    except hyperopt.exceptions.AllTrialsFailed:
      best = None
    if upload and not online:
      trials.upload()
    return trials, best

  def test_upload_trials(self):
    trials, _ = self.run_fmin(upload=False)
    tids = upload_trials('hyperopt-integration-test', trials)
    self._verify_uploaded_trials(trials, tids)

  def test_trials_delete_all(self):
    trials, _ = self.run_fmin(upload=True)
    assert(len(trials) > 0 and len(trials) == len(trials.uploaded_tids))
    trials.delete_all()
    assert(len(trials) == 0 and len(trials.uploaded_tids) == 0)

  @pytest.mark.parametrize("online, upload, wrap, max_evals",
                           [
                             (False, True, None, 3),
                             (True, True, None, 3),
                             (False, False, None, 3),
                             (True, True, 'mongo', 3),
                             (True, True, 'spark', 3),
                            ])
  @pytest.mark.parametrize("objective",
                           [objective_random,
                            objective_success,
                            objective_fail])
  def test_fmin(self, online, upload, objective, wrap, max_evals):
    trials, best = self.run_fmin(online, upload, objective, max_evals=max_evals, wrap=wrap)
    self._verify_best_trial(best, trials, objective)
    self._verify_runs(trials, upload, max_evals)


  def _verify_best_trial(self, best, trials, objective):
    if objective is objective_fail:
      assert best is None
    if objective is objective_success:
      assert best is not None
    losses = [r['loss'] for r in trials.results if r['status'] == STATUS_OK]
    assert ((not best) and (not losses)) or (best and losses)
    if best:
      loss = objective_success(best)['loss']
      assert loss == min(losses)

  def _verify_runs(self, trials, upload, max_evals):
    if not upload:
      assert len(trials.uploaded_tids) == 0
      return
    assert len(trials.uploaded_tids) == max_evals
    self._verify_uploaded_trials(trials, trials.uploaded_tids)

  def _verify_uploaded_trials(self, trials, uploaded_tids):
    trial_dict = {tid: (result, parameters)
                  for tid, result, parameters in zip(trials.tids, trials.results,
                                                     trials.parameters)}

    def run_result(run):
      result = {}
      if run.state == "completed":
        result['status'] = STATUS_OK
        for m in run.values:
          result[m] = run.values[m].value
      elif run.state == "failed":
        result['status'] = STATUS_FAIL
      else:
        result['status'] = None
      return result

    def run_parameters(run):
      return dict(run.assignments)

    run_dict = {}
    for tid, run_id in uploaded_tids.items():
      run = sigopt.get_run(run_id)
      run_dict[tid] = (run_result(run), run_parameters(run))

    assert trial_dict == run_dict
