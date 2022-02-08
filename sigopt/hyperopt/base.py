from .compat import Trials, STATUS_OK, STATUS_FAIL
from ..dict_run_context import DictRunContext
from .. import SigOptFactory
from ..defaults import get_default_name


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

  def validate_trial(self, trial):
    if 'result' not in trial:
      raise ValueError('No result found in trial')
    result = trial['result']
    if 'status' not in result:
      raise ValueError('No status found in trial result')

  def trial_to_run(self, trial):
    self.validate_trial(trial)
    metadata = {'optimizer': 'hyperopt'}
    result = trial['result']
    metrics = {k:v for k, v in result.items() if isinstance(v, (int, float))}
    parameters = self.trial_parameters(trial)
    status = result.get('status')
    run = DictRunContext(name=get_default_name(self.factory.project), metadata=metadata)
    run.log_parameters(
      parameters,
      source=HYPEROPT_SOURCE_NAME,
      source_meta={
        'sort': HYPEROPT_SOURCE_PRIORITY,
        'default_show': True
      })
    if status == STATUS_OK:
      if not metrics:
        raise ValueError('No metrics found in trial result')
      run.log_metrics(metrics)
      run.log_state('completed')
    elif status == STATUS_FAIL:
      run.log_failure()
    else:
      raise ValueError(f'status must be {STATUS_OK} or {STATUS_FAIL}, actully {status}')
    return run.get()

  def _upload(self, trials):
    runs = [self.trial_to_run(trial) for trial in trials]
    runs = self.factory.upload_runs(runs)
    return {trial['tid']:run.id for trial, run in zip(trials, runs)}

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

  def delete_all(self):
    self.uploaded_tids.clear()
    self._trials.delete_all()

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
    except AttributeError as e:
      raise AttributeError(f"{type(self.__name__)} object has no attribute {name}") from e


def upload_trials(project, trials):
  st = SigOptTrials(project=project, online=False)
  return st.upload(trials)
