from .compat import Trials, STATUS_OK, STATUS_FAIL, fmin
from .. import SigOptFactory

HYPEROPT_SOURCE_NAME = 'Hyperopt Suggest'
HYPEROPT_SOURCE_PRIORITY = 1

class SigOptTrials(Trials):
  def __init__(self, project, trials=None, online=True):
    self.factory = SigOptFactory(project)
    self.online = online
    self._trials = trials if trials else Trials()
    self.uploaded_tids = {}

  @property
  def _dynamic_trials(self):
    return self._trials._dynamic_trials


  @property
  def parameters(self):
    return [self.trial_parameters(trial) for trial in self.trials]

  def upload(self, trials=None):
    new_trials = []
    trials = trials if trials is not None else self.trials
    for trial in trials:
      result = trial['result']
      status = result.get('status')
      if status in [STATUS_OK, STATUS_FAIL]:
        tid = trial['tid']
        if tid not in self.uploaded_tids:
          new_trials.append(trial)
    ids = self._upload(new_trials)
    self.uploaded_tids.update(ids)
    return ids


  def _upload(self, trials):
    ids = {}
    for trial in trials:
      tid = trial['tid']
      result = trial['result']
      metrics = {k:v for k, v in result.items() if isinstance(v, (int, float))}
      parameters = self.trial_parameters(trial)
      metadata = {'optimizer': 'hyperopt'}
      status = result.get('status')
      run = self.factory.create_run(metadata=metadata)
      with run:
        self.log_run_params(run, parameters)
        if status == STATUS_OK:
          run.log_metrics(metrics)
        elif status == STATUS_FAIL:
          run.log_failure()
        else:
          raise ValueError(f'status must be {STATUS_OK} or {STATUS_FAIL}, actully {status}')
      ids[tid] = run.id
    return ids

  def log_run_params(self, run, params):
    run.set_parameters_sources_meta(
      HYPEROPT_SOURCE_NAME,
      sort=HYPEROPT_SOURCE_PRIORITY,
      default_show=True
    )
    run.set_parameters(params)
    run.set_parameters_source(params, HYPEROPT_SOURCE_NAME)


  def trial_parameters(self, trial):
    vals = trial.get('misc', {}).get('vals', {})
    rval = {}
    for k, v in vals.items():
      if v:
        rval[k] = v[0]
    return rval

  def do_refresh(self):
    if self.online:
      self.upload()

  # Wrapped APIs

  def view(self, exp_key=None, refresh=True):
    return self._tails.view(exp_key, refresh)

  def aname(self, trial, name):
    return self.aname(trial, name)

  def trial_attachments(self, trial):
    return self._trials.trial_attachments(trial)

  def __iter__(self):
    return iter(self._trials)

  def __len__(self):
    return len(self._trials)

  def __getitem__(self, item):
    return self._trials[item]

  def refresh(self):
    r = self._trials.refresh()
    self.do_refresh()
    return r

  @property
  def trials(self):
    return self._trials.trials

  @property
  def tids(self):
    return self._trials.tids

  @property
  def specs(self):
    return self._trials.specs

  @property
  def results(self):
    return self._trials.results

  @property
  def miscs(self):
    return self._trials.miscs

  @property
  def idxs_vals(self):
    return self._trials.idxs_vals

  @property
  def idxs(self):
    return self._trials.idxs

  @property
  def vals(self):
    return self._trials.vals

  def assert_valid_trial(self, trial):
    return self._trials.assert_valid_trial(trial)

  def insert_trial_doc(self, doc):
    return self._trials.insert_trial_doc(doc)

  def insert_trial_docs(self, docs):
    return self._trials.insert_trial_docs(docs)

  def new_trial_ids(self, n):
    return self._trials.new_trial_ids(n)

  def new_trial_docs(self, tids, specs, results, miscs):
    return self._trials.new_trial_docs(tids, specs, results, miscs)

  def source_trial_docs(self, tids, specs, results, miscs, sources):
    return self._trials.source_trial_docs(tids, specs, results, miscs, sources)

  def delete_all(self):
    self.uploaded_tids.clear()
    return self._trials.delete_all()

  def count_by_state_synced(self, arg, trials=None):
    return self._trials.count_by_state_synced(arg, trials)

  def count_by_state_unsynced(self, arg):
    return self._trials.count_by_state_unsynced(arg)

  def losses(self, bandit=None):
    return self._trials.losses(bandit)

  def statuses(self, bandit=None):
    return self._trials.statuses(bandit)

  def average_best_error(self, bandit=None):
    return self._trials.average_best_error(bandit)

  @property
  def best_trial(self):
    return self._trials.best_trial

  @property
  def argmin(self):
    return self._trials.argmin

  def fmin(
      self,
      fn,
      space,
      algo=None,
      max_evals=None,
      timeout=None,
      loss_threshold=None,
      max_queue_len=1,
      rstate=None,
      verbose=False,
      pass_expr_memo_ctrl=None,
      catch_eval_exceptions=False,
      return_argmin=True,
      show_progressbar=True,
      early_stop_fn=None,
      trials_save_file="",
  ):
    return fmin(
      fn,
      space,
      algo=algo,
      max_evals=max_evals,
      timeout=timeout,
      loss_threshold=loss_threshold,
      trials=self,
      rstate=rstate,
      verbose=verbose,
      max_queue_len=max_queue_len,
      allow_trials_fmin=False,  # -- prevent recursion
      pass_expr_memo_ctrl=pass_expr_memo_ctrl,
      catch_eval_exceptions=catch_eval_exceptions,
      return_argmin=return_argmin,
      show_progressbar=show_progressbar,
      early_stop_fn=early_stop_fn,
      trials_save_file=trials_save_file,
    )

def upload_trials(project, trials):
  st = SigOptTrials(project=project, online=False)
  return st.upload(trials)
