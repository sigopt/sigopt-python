import json
import threading

from .run_factory import BaseRunFactory
from .run_context import global_run_context
from .objects import Parameter
from .validate.aiexperiment_input import validate_aiexperiment_update_input


class AIExperimentContext(BaseRunFactory):
  '''Wraps the AIExperiment object and provides extra utility methods.'''

  def __init__(self, aiexperiment, connection):
    self._aiexperiment = aiexperiment
    self._refresh_lock = threading.Lock()
    self._connection = connection

  def refresh(self):
    '''Refresh the state of the AIExperiment from the SigOpt API.'''
    connection = self._connection
    with self._refresh_lock:
      self._aiexperiment = connection.aiexperiments(self.id).fetch()

  def is_finished(self):
    '''Check if the AIExperiment has consumed its entire budget.'''
    self.refresh()
    return self.progress.remaining_budget is not None and self.progress.remaining_budget <= 0

  def loop(self, name=None):
    '''Create runs until the AIExperiment has finished.'''
    while not self.is_finished():
      yield self.create_run(name=name)

  def archive(self):
    connection = self._connection
    connection.aiexperiments(self.id).delete()
    self.refresh()

  @property
  def project(self):
    # delegate to __getattr__
    raise AttributeError

  def __getattr__(self, attr):
    return getattr(self._aiexperiment, attr)

  def _create_run(self, name, metadata):
    aiexperiment = self._aiexperiment
    connection = self._connection
    run = connection.aiexperiments(aiexperiment.id).training_runs().create(
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
    return self._connection.aiexperiments(self.id).best_training_runs().fetch().iterate_pages()

  def _parse_parameter(self, parameter):
    if isinstance(parameter, Parameter):
      parameter = parameter.as_json(parameter)
      for attr in ['constraints', 'conditions']:
        if not parameter.get(attr):
          parameter.pop(attr, None)
    return parameter

  def update(self, **kwargs):
    if 'parameters' in kwargs:
      parameters = [self._parse_parameter(p) for p in kwargs['parameters']]
      kwargs['parameters'] = parameters
    kwargs = validate_aiexperiment_update_input(kwargs)
    return self._connection.aiexperiments(self.id).update(**kwargs)
