import contextlib
import functools

import requests

from .config import config
from .exception import ApiException, RunException
from .interface import get_connection
from .lib import remove_nones
from .objects import Suggestion, TrainingRun
from .runs.utils import sanitize_number, validate_name, create_api_image_payload, get_blob_properties


_UNSET = object()

class NoDefaultParameterError(RunException):
  def __init__(self, parameter_name):
    super().__init__(f'No default provided for parameter "{parameter_name}"')

class BaseRunContext(object):
  @property
  def id(self):
    raise NotImplementedError

  def _log_dataset(self, name):
    raise NotImplementedError

  def _get_parameter(self, name, default):
    raise NotImplementedError

  def _log_failure(self):
    raise NotImplementedError

  def _log_metadata(self, metadata):
    raise NotImplementedError

  def _log_metrics(self, metrics):
    raise NotImplementedError

  def _log_model(self, type):
    raise NotImplementedError

  def _log_source_code(self, source_code):
    raise NotImplementedError

  def _update_logs(self, logs):
    raise NotImplementedError

  def _log_checkpoint(self, values):
    raise NotImplementedError

  def _log_image(self, name, payload):
    raise NotImplementedError

  def _end(self):
    raise NotImplementedError

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
    return self._get_parameter(name, default)

  def log_dataset(self, name):
    '''
    sigopt.log_dataset(name)
      Logs a dataset that will be used for your Run.
    name: string, required
      The name of the dataset you would like to track.
    '''
    validate_name('dataset name', name)
    self._log_dataset(name)

  def log_failure(self):
    '''
    sigopt.log_failure()
      Indicates that the Run has failed for any reason.
    '''
    self._log_failure()

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
    if value is not None and not isinstance(value, str):
      try:
        value = sanitize_number('metadata', key, value)
      except ValueError:
        value = str(value)
    return self._log_metadata({key: value})

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
    metric_log = {}
    metric_log['value'] = sanitize_number('metric', name, value)
    if stddev is not None:
      metric_log['value_stddev'] = sanitize_number('metric stddev', name, stddev)
    self._log_metrics({name: metric_log})

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
    self._log_model(type)

  def log_source_code(self, **source_code):
    self._log_source_code(source_code)

  def update_logs(self, logs):
    self._update_logs(logs)

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
    self._log_checkpoint(checkpoint_values)

  def log_image(self, image, name=None):
    '''
    sigopt.log_image(image, name=None)
      Logs an image artifact from your model's evaluation. See the documentation for more details:
      https://app.sigopt.com/docs/runs/reference#log_image
    image: string, PIL.Image.Image, matplotlib.figure.Figure or numpy.ndarray, required
      The image artifact to upload. This will be converted to an appropriate format and then uploaded.
    name: string
      An optional name to give your uploaded image.
    '''
    if name is not None:
      validate_name('image name', name)
    payload = create_api_image_payload(image)
    if payload is None:
      return
    self._log_image(name, payload)

  def end(self, exception=None):
    '''
    run.end(exception=None)
      Stops the run. In most cases it should be easier to use your run in a context manager instead, ex.
      with run:
        ...
    exception: instanceof(Exception)
      The exception that occurred that caused the termination of the run. Not needed if the run ended gracefully.
    '''
    self._end()


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

    @functools.wraps(wrapped_function)
    def function_impl(self, *args, **kwargs):
      checkpoint_values = wrapped_function(self, *args, **kwargs)
      self._create_checkpoint({'values': checkpoint_values})

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

class RunContext(BaseRunContext):
  def __init__(
    self,
    connection,
    run,
    suggestion,
  ):
    super().__init__()
    self.connection = connection
    self.run = run
    self.suggestion = suggestion

  def to_json(self):
    data = {"run": self.run.to_json()}
    if self.suggestion is not None:
      data["suggestion"] = self.suggestion.to_json()
    return data

  @classmethod
  def from_json(cls, data):
    suggestion = data.get("suggestion")
    if suggestion is not None:
      suggestion = Suggestion(data)
    run = TrainingRun(data["run"])
    return cls(get_connection(), run, suggestion)

  @property
  def id(self):
    return self.run.id

  def __enter__(self):
    return self

  def __exit__(self, type, value, tb):
    self._end(exception=value)

  def _end(self, exception=None):
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
      'Run finished, view it on the SigOpt dashboard at https://app.sigopt.com/run/{run_id}'.format(
        run_id=self.run.id,
      )
    )

  def _request(self, method, path, params, headers=None):
    base_url = self.connection.impl.api_url
    run_id = self.run.id
    return self.connection.impl._request(
      method=method,
      url=f'{base_url}/v1/training_runs/{run_id}{path}',
      params=params,
      headers=headers,
    )

  def _update_run(self, body):
    self._request(
      method='MERGE',
      path='',
      params=body,
      headers={'X-Response-Content': 'skip'},
    )

  def _create_checkpoint(self, body):
    self._request(
      method='POST',
      path='/checkpoints',
      params=body,
      headers={'X-Response-Content': 'skip'},
    )

  @updates('assignments', returns=UPDATE_AND_RETURN)
  def _get_parameter(self, name, default=_UNSET):
    value = default
    if self.suggestion is not None:
      value = self.suggestion.assignments.get(name, value)
    if value is _UNSET:
      raise NoDefaultParameterError(name)
    return {name: value}, value

  @updates('datasets', returns=UPDATE)
  def _log_dataset(self, name):
    return {name: {}}

  @updates('state', returns=UPDATE)
  def _log_failure(self):
    return 'failed'

  @updates('metadata', returns=UPDATE)
  def _log_metadata(self, metadata):
    return metadata

  @updates('values')
  def _log_metric(self, metrics):
    return metrics

  @updates('model', returns=UPDATE)
  def _log_model(self, type):
    return remove_nones({'type': type})

  @updates('source_code', returns=UPDATE)
  def _log_source_code(self, source_code):
    return source_code

  @updates('logs', returns=UPDATE)
  def _update_logs(self, logs):
    return logs

  @creates_checkpoint()
  def _log_checkpoint(self, values):
    return values

  def _log_image(self, image, name):
    payload = create_api_image_payload(image)
    if payload is None:
      return
    filename, image_data, content_type = payload
    with image_data:
      content_length, content_md5_base64 = get_blob_properties(image_data)
      file_info = self._request(
        method='POST',
        path='/files',
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

class GlobalRunContext(BaseRunContext):
  '''
  If a RunContext is available then methods will call the RunContext.
  Fallback to noop.
  '''
  CONFIG_CONTEXT_KEY = "global_run_context"

  def __init__(self, run_context):
    self._run_context = run_context

  @property
  def id(self):
    if self._run_context is None:
      return None
    return self._run_context.id

  @property
  def run_context(self):
    return self._run_context

  def set_run_context(self, run_context):
    self._run_context = run_context

  def clear_run_context(self):
    self._run_context = None

  def to_json(self):
    if self._run_context is None:
      return None
    return self._run_context.to_json()

  @classmethod
  def from_config(cls, config_):
    data = config_.get_context_data(cls)
    run_context = None
    if data is not None:
      run_context = RunContext.from_json(data)
    return cls(run_context)

def delegate_to_run_context(method_name):

  def func(self, *args, **kwargs):
    run_context = self.run_context
    if run_context is not None:
      getattr(run_context, method_name)(*args, **kwargs)

  setattr(GlobalRunContext, method_name, func)


for method_name in [
  "_log_dataset",
  "_log_failure",
  "_log_metadata",
  "_log_metrics",
  "_log_model",
  "_log_checkpoint",
  "_log_image",
]:
  delegate_to_run_context(method_name)

global_run_context = GlobalRunContext.from_config(config)
