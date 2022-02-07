from ..run_context import BaseRunContext
import copy

class DictRunContext(BaseRunContext):
  def __init__(self, **kwargs):
    self.run = copy.deepcopy(kwargs) if kwargs else {}

  def get(self, name=None, type=dict):
    if name is None:
      return self.run
    if not name in self.run:
      self.run[name] = type()
    return self.run[name]

  def log_state(self, state):
    self.run['state'] = state

  def _set_parameters(self, parameters):
    self.get('assignments').update(parameters)

  def _log_failure(self):
    self.run['state'] = 'failed'

  def _log_metadata(self, metadata):
    self.get('metadata').update(metadata)

  def _log_metrics(self, metrics):
    self.get('values').update(metrics)

  def _set_parameters_meta(self, parameters_meta):
    self.get('assignments_meta').update(parameters_meta)

  def _set_parameters_sources(self, assignments_sources):
    self.get('assignments_sources').update(assignments_sources)

  def log_parameters(self, params, source=None, source_meta=None):
    self.set_parameters(params)
    if source is not None:
      self.set_parameters_source(params, source)
    if source_meta is not None:
      self.set_parameters_sources_meta(source, **source_meta)
