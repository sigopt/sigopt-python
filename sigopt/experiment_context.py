import json
import threading

from .run_factory import BaseRunFactory
from .run_context import global_run_context
from .objects import Parameter


class ExperimentContext(BaseRunFactory):
  '''Wraps the Experiment object and provides extra utility methods.'''

  def __init__(self, experiment, connection):
    if experiment.project is None:
      raise ValueError("experiment does not belong to a project")
    self._experiment = experiment
    self._refresh_lock = threading.Lock()
    self._connection = connection

  def refresh(self):
    '''Refresh the state of the Experiment from the SigOpt API.'''
    connection = self._connection
    with self._refresh_lock:
      self._experiment = connection.experiments(self.id).fetch()

  def is_finished(self):
    '''Check if the experiment has consumed its entire budget.'''
    self.refresh()
    return self.progress.remaining_budget is not None and self.progress.remaining_budget <= 0

  def loop(self, name=None):
    '''Create runs until the experiment has finished.'''
    while not self.is_finished():
      yield self.create_run(name=name)

  def archive(self):
    connection = self._connection
    connection.experiments(self.id).delete()
    self.refresh()

  @property
  def project(self):
    # delegate to __getattr__
    raise AttributeError

  def __getattr__(self, attr):
    return getattr(self._experiment, attr)

  def _create_run(self, name, metadata):
    experiment = self._experiment
    connection = self._connection
    run = connection.experiments(experiment.id).training_runs().create(
      name=name,
      metadata=metadata,
    )
    run_context = self.run_context_class(connection, run, global_run_context.params)
    return run_context

  def get_runs(self):
    return self._connection.clients(self.client).projects(self.project).training_runs().fetch(filters=json.dumps([{
      "field": "experiment",
      "operator": "==",
      "value": self.id,
    }])).iterate_pages()

  def get_best_runs(self):
    return self._connection.experiments(self.id).best_training_runs().fetch().iterate_pages()

  def _parse_parameter(self, parameter):
    if isinstance(parameter, Parameter):
      parameter = parameter.as_json(parameter)
      for attr in ['constraints', 'conditions']:
        parameter.pop(attr, None)
    return parameter

  def update(self, **kwargs):
    if 'parameters' in kwargs:
      parameters = [self._parse_parameter(p) for p in kwargs['parameters']]
      kwargs['parameters'] = parameters
    return self._connection.experiments(self.id).update(**kwargs)
