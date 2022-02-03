from .compat import Trials, STATUS_OK, STATUS_FAIL, fmin
from .. import SigOptFactory

HYPEROPT_SOURCE_NAME = 'Hyperopt Suggest'
HYPEROPT_SOURCE_PRIORITY = 1


class SigOptTrials(object):
  def __init__(self, project, trials=None, online=True):
    self.factory = SigOptFactory(project)
    self.online = online
    self._trials = trials if trials else Trials()
    self.uploaded_tids = {}

    if online:
      self.saved_refresh = getattr(self._trials, 'refresh')
      def new_refresh():
        r = self.saved_refresh()
        self.do_refresh()
        return r
      setattr(self._trials, 'refresh', new_refresh)

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

  def __iter__(self):
    return iter(self._trials)

  def __len__(self):
    return len(self._trials)

  def __getitem__(self, item):
    return self._trials[item]

  def __getattr__(self, name):
    attrs = dir(self)
    if name in attrs:
      return attrs[name]
    try:
      return getattr(self._trials, name)
    except AttributeError:
      raise AttributeError(f"{type(self.__name__)} object has no attribute {name}")


def upload_trials(project, trials):
  st = SigOptTrials(project=project, online=False)
  return st.upload(trials)
