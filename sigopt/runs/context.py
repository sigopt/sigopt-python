import requests
import warnings

from ..exception import ApiException, RunException
from ..objects import Suggestion, TrainingRun
from ..vendored import six
from .defaults import ensure_project_exists, get_default_name, get_default_project
from .utils import sanitize_number, validate_name, create_api_image_payload, get_blob_properties
from ..lib import get_app_url

def remove_nones(mapping):
  return {key: value for key, value in mapping.items() if value is not None}

_UNSET = object()

class NoDefaultParameterException(RunException):
  def __init__(self, parameter_name):
    super(NoDefaultParameterException, self).__init__(
      six.u('No default provided for parameter "{}"').format(parameter_name)
    )

class BaseRunContext(object):
  def log_assignments(self, assignments):
    raise NotImplementedError()

  def set_parameters(self, values):
    raise NotImplementedError()

  def get_parameter(self, name, default=_UNSET):
    raise NotImplementedError()

  def log_dataset(self, name):
    raise NotImplementedError()

  def log_failure(self):
    raise NotImplementedError()

  def log_metadata(self, key, value):
    raise NotImplementedError()

  def log_metric(self, name, value, stddev=None):
    raise NotImplementedError()

  def log_model(self, type=None):
    raise NotImplementedError()

  def log_source_code(self, **source_code):
    raise NotImplementedError()

  def update_logs(self, logs):
    raise NotImplementedError()

  def log_checkpoint(self, values):
    raise NotImplementedError()

  def log_image(self, image, name=None):
    raise NotImplementedError()

class NullRunContext(BaseRunContext):
  def __init__(self):
    super(NullRunContext, self).__init__()
    self._manual_parameter_values = {}
    self.run_id = None

  def log_assignments(self, assignments):
    pass

  def set_parameters(self, values):
    values = dict(values)
    self._manual_parameter_values.update(values)

  def get_parameter(self, name, default=_UNSET):
    value = self._manual_parameter_values.get(name, default)
    if value is _UNSET:
      raise NoDefaultParameterException(name)
    return value

  def log_dataset(self, name):
    pass

  def log_failure(self):
    pass

  def log_metadata(self, key, value):
    pass

  def log_metric(self, name, value, stddev=None):
    pass

  def log_model(self, type=None):
    pass

  def log_source_code(self, **source_code):
    pass

  def update_logs(self, logs):
    pass

  def log_checkpoint(self, values):
    pass

  def log_image(self, image, name=None):
    pass


UPDATE = object()
UPDATE_AND_RETURN = object()

def updates(update_key, returns=UPDATE):

  def function_wrapper(wrapped_function):

    def function_impl(self, *args, **kwargs):
      raw_return = wrapped_function(self, *args, **kwargs)
      if returns is UPDATE_AND_RETURN:
        update_value, return_value = raw_return
      else:
        update_value, return_value = raw_return, None
      self._update_run({update_key: update_value})
      return return_value

    function_impl.__doc__ = wrapped_function.__doc__
    return function_impl

  return function_wrapper

def creates_checkpoint():

  def function_wrapper(wrapped_function):

    def function_impl(self, *args, **kwargs):
      checkpoint_values = wrapped_function(self, *args, **kwargs)
      self._create_checkpoint({'values': checkpoint_values})

    function_impl.__doc__ = wrapped_function.__doc__
    return function_impl

  return function_wrapper

def allow_state_update(new_state, old_state):
  if new_state == old_state:
    return False
  precedence = {
    'failed': 2,
    'completed': 1,
  }
  new_state_precedence = precedence.get(new_state, 0)
  old_state_precedence = precedence.get(old_state, 0)
  return new_state_precedence >= old_state_precedence

class LiveRunContext(BaseRunContext):
  RUN_KEY = 'run'
  SUGGESTION_KEY = 'suggestion'

  @classmethod
  def create(
    cls,
    connection,
    run_name=None,
    project_id=None,
    suggestion=None,
    all_assignments=None
  ):
    project_id = project_id or get_default_project()
    run_name = run_name or get_default_name(project_id)
    client_id = connection.tokens('self').fetch().client
    ensure_project_exists(connection, client_id, project_id)
    if suggestion is not None:
      connection.experiments(suggestion.experiment).update(project=project_id)
    suggestion_id = None if suggestion is None else suggestion.id
    run = connection.clients(client_id).projects(project_id).training_runs().create(
      name=run_name,
      suggestion=suggestion_id,
    )
    run_context = cls(connection, run, suggestion)
    print(
      'Run started, view it on the SigOpt dashboard at {app_url}/run/{run_id}'.format(
        app_url=get_app_url(),
        run_id=run.id,
      )
    )
    if all_assignments:
      run_context.log_assignments(all_assignments)
    return run_context

  def to_json(self):
    return {
      self.RUN_KEY: self.run.to_json(),
      self.SUGGESTION_KEY: self.suggestion and self.suggestion.to_json(),
    }

  @classmethod
  def from_json(cls, connection, data):
    if data is None:
      return None
    run = TrainingRun(data[cls.RUN_KEY])
    suggestion_data = data.get(cls.SUGGESTION_KEY)
    suggestion = None
    if suggestion_data:
      suggestion = Suggestion(suggestion_data)
    return cls(
      connection,
      run=run,
      suggestion=suggestion,
    )

  def __init__(
    self,
    connection,
    run,
    suggestion,
  ):
    super(LiveRunContext, self).__init__()
    self.connection = connection
    self.run = run
    self.suggestion = suggestion
    self._previously_logged_metric_names = set()
    self._manual_parameter_values = {}

  @property
  def run_id(self):
    return self.run.id

  def __enter__(self):
    return self

  def __exit__(self, type, value, tb):
    self.end(exception=value)

  def end(self, exception=None):
    old_run_state = self.connection.training_runs(self.run.id).fetch().state
    new_run_state = 'failed' if exception else 'completed'
    if allow_state_update(new_run_state, old_run_state):
      self._update_run({'state': new_run_state})
    if self.suggestion:
      try:
        (self.connection.experiments(self.suggestion.experiment)
          .observations()
          .create(training_run=self.run.id))
      except ApiException as e:
        if e.status_code == 400:
          self.connection.experiments(self.suggestion.experiment).observations().create(
            failed=True,
            training_run=self.run.id,
          )
        else:
          raise
    print(
      'Run finished, view it on the SigOpt dashboard at {app_url}/run/{run_id}'.format(
        app_url=get_app_url(),
        run_id=self.run.id,
      )
    )

  def _update_run(self, body):
    self.connection.impl._request(
      method='MERGE',
      url=six.u('{base_url}/v1/training_runs/{run_id}').format(
        base_url=self.connection.impl.api_url,
        run_id=self.run.id,
      ),
      params=body,
      headers={'X-Response-Content': 'skip'},
    )

  def _create_checkpoint(self, body):
    self.connection.impl._request(
      method='POST',
      url=six.u('{base_url}/v1/training_runs/{run_id}/checkpoints').format(
        base_url=self.connection.impl.api_url,
        run_id=self.run.id,
      ),
      params=body,
      headers={'X-Response-Content': 'skip'},
    )

  @updates('assignments', returns=UPDATE)
  def log_assignments(self, assignments):
    return assignments

  @updates('assignments', returns=UPDATE)
  def set_parameters(self, values):
    '''
    sigopt.set_parameters(name, values)
      Sets a dictionary of parameter values to use.
      These values override the default value provided to sigopt.get_parameter,
      but they will not override the paremeter values used in the sigopt optimization context.
    values: dict, required
      The dictionary of parameter values to use.
    '''
    values = dict(values)
    if self.suggestion is not None:
      for parameter_name in self.suggestion.assignments:
        values.pop(parameter_name, None)
    self._manual_parameter_values.update(values)
    return values

  @updates('assignments', returns=UPDATE_AND_RETURN)
  def get_parameter(self, name, default=_UNSET):
    '''
    sigopt.get_parameter(name, default)
      Tracks and returns an assignment value for your model.
      Normally returns the default value,
      except in the sigopt optimize context the returned value is generated from a SigOpt Experiment's Suggestion.
    name: string, required
      The name of the assignment that you would like to track.
    default: number/string, required
      The value of the assignment to use when no other value is available.
    returns: number/string
      The value to use for this assignment in your code.
      Returns the default when no value is available.
    '''
    value = default
    value = self._manual_parameter_values.get(name, value)
    if self.suggestion is not None:
      value = self.suggestion.assignments.get(name, value)
    if value is _UNSET:
      raise NoDefaultParameterException(name)
    return {name: value}, value

  @updates('datasets', returns=UPDATE)
  def log_dataset(self, name):
    '''
    sigopt.log_dataset(name, version=None, type=None)
      Logs a dataset that will be used for your Run.
    name: string, required
      The name of the dataset you would like to track.
    '''
    return {name: {}}

  @updates('state', returns=UPDATE)
  def log_failure(self):
    '''
    sigopt.log_failure()
      Indicates that the Run has failed for any reason.
    '''
    return 'failed'

  @updates('metadata', returns=UPDATE)
  def log_metadata(self, key, value):
    '''
    sigopt.log_metadata(key, value)
      Stores some extra information about your Run.
    key: string, required
      The metadata key that your would like to store.
    value: number/object, required
      The value of the metadata that you would like to track.
      If value is not a number then it will be logged as a string.
    '''
    validate_name('metadata key', key)
    if value is not None and not isinstance(value, six.string_types):
      try:
        value = sanitize_number('metadata', key, value)
      except ValueError:
        value = str(value)
    return {key: value}

  @updates('values')
  def log_metric(self, name, value, stddev=None):
    '''
    sigopt.log_metric(name, value, stddev=None)
      Logs a metric value from your model's evaluation.
    name: string, required
      The name of the metric that you would like to track.
    value: number, required
      The value of the metric to track.
    stddev: number
      The standard deviation of the metric to track.
    '''
    validate_name('metric name', name)
    if name in self._previously_logged_metric_names:
      warnings.warn(
        six.u('The metric with name "{}" has already been logged, overwriting the previous value').format(name),
        RuntimeWarning,
      )
    self._previously_logged_metric_names.add(name)
    metric_log = {}
    metric_log['value'] = sanitize_number('metric', name, value)
    if stddev is not None:
      metric_log['value_stddev'] = sanitize_number('metric stddev', name, stddev)
    return {name: metric_log}

  @updates('model', returns=UPDATE)
  def log_model(self, type=None):
    '''
    sigopt.log_model(type=None)
      Logs information about your model.
      This will be converted to a string before it is tracked.
    type: object
      The model object being tracked, or a string representing the type of model.
      The str builtin will be used to convert your model to a string.
    '''
    if type is not None:
      type = str(type)
    return remove_nones({'type': type})

  @updates('source_code', returns=UPDATE)
  def log_source_code(self, **source_code):
    return source_code

  @updates('logs', returns=UPDATE)
  def update_logs(self, logs):
    return logs

  @creates_checkpoint()
  def log_checkpoint(self, values):
    '''
    sigopt.log_checkpoint(values)
      Logs a checkpoint from your model's evaluation.
    values: dict
      A mapping of the metric names to the values they take for the current checkpoint.
    '''
    if not isinstance(values, dict):
      raise ValueError('values must be a dict')
    checkpoint_values = []
    for name, value in values.items():
      validate_name('metric name', name)
      if value is not None:
        checkpoint_values.append({
          'name': name,
          'value': sanitize_number('metric_stddev', name, value),
        })
    return checkpoint_values

  def log_image(self, image, name=None):
    payload = create_api_image_payload(image)
    if payload is None:
      return
    filename, image_data, content_type = payload
    with image_data:
      content_length, content_md5_base64 = get_blob_properties(image_data)
      file_info = self.connection.impl._request(
        method='POST',
        url=six.u('{base_url}/v1/training_runs/{run_id}/files').format(
          base_url=self.connection.impl.api_url,
          run_id=self.run.id,
        ),
        params={
          "content_length": content_length,
          "content_md5": content_md5_base64,
          "content_type": content_type,
          "name": name,
          "filename": filename,
        },
      )
      upload_info = file_info["upload"]
      image_data.seek(0)
      response = requests.request(
        upload_info["method"],
        upload_info["url"],
        headers=upload_info["headers"],
        data=image_data,
      )
      response.raise_for_status()
