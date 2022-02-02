from hyperopt import fmin, tpe, hp, STATUS_OK, STATUS_FAIL, Trials
import hyperopt
from sigopt.hyperopt import SigOptTrials, upload_trials
import sigopt
import numpy as np
import pytest

def objective(p, threshold=0.8):
  x, y = p['x'], p['y']
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


class TestHyperopt(object):
  def run_fmin(self, online=True, upload=True, threshold=0.5, max_evals=3):
    project = 'hyperopt-integration-test'
    trials = SigOptTrials(project=project, online=(online and upload))
    try:
      best = fmin(lambda x: objective(x, threshold),
                  space={
                    'x' : hp.uniform('x', -10, 10),
                    'y': hp.uniform('y', -10, 10)
                  },
                  algo=tpe.suggest,
                  max_evals=max_evals,
                  trials=trials)
    except hyperopt.exceptions.AllTrialsFailed:
      best = None
    if upload and (online == False):
      trials.upload()
    return trials, best

  def test_upload_trials(self):
    trials, _ = self.run_fmin(upload=False)
    tids = upload_trials('hyperopt-integration-test', trials)
    self._verify_uploaded_trials(trials, tids)

  @pytest.mark.parametrize("online, upload",
                           [(False, True),
                            (True, True),
                            (False, False),
                            ])
  @pytest.mark.parametrize("threshold", [-1.0, 0.5, 1.0])
  def test_fmin(self, online, upload, threshold, max_evals=3):
    trials, best = self.run_fmin(online, upload, threshold, max_evals)
    self._verify_best_trial(best, trials, threshold)
    self._verify_runs(trials, upload, max_evals)

  def _verify_best_trial(self, best, trials, threshold):
    if threshold < 0:
      assert not best
    if threshold >= 1.0:
      assert best
    losses = [r['loss'] for r in trials.results if r['status'] == STATUS_OK]
    assert ((not best) and (not losses)) or (best and losses)
    if best:
      loss = objective(best, 1.0)['loss']
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
        resutl['status'] = None
      return result

    def run_parameters(run):
      return dict(run.assignments)

    run_dict = {}
    for tid, run_id in uploaded_tids.items():
      run = sigopt.get_run(run_id)
      run_dict[tid] = (run_result(run), run_parameters(run))

    assert trial_dict == run_dict
