import functools

import requests

from .config import config
from .exception import RunException
from .file_utils import create_api_image_payload, get_blob_properties
from .interface import get_connection
from .lib import remove_nones, sanitize_number, validate_name, is_mapping, is_string
from .sigopt_logging import print_logger
from .objects import TrainingRun
from .run_params import RunParameters, GlobalRunParameters


_UNSET = object()

def maybe_truncate_log(log_content):
  # If log content is extremely long, preserve some useful content instead of failing.
  # TODO(patrick): Support streaming logs to avoid this
  max_size = 1024
  if len(log_content) >= max_size:
    truncated_disclaimer = '[ WARNING ] The max size has been reached so these logs have been truncated'
    half = max_size // 2
    head = log_content[:half]
    tail = log_content[-half:]
    log_content = '\n\n'.join([
      truncated_disclaimer,
      head,
      '... truncated ...',
      tail,
    ])
  return log_content

class NoDefaultParameterError(RunException):
  def __init__(self, parameter_name):
    super().__init__(f'No default provided for parameter "{parameter_name}"')

class BaseRunContext(object):
  @property
  def id(self):
    raise NotImplementedError

  @property
  def experiment(self):
    return None

  @property
  def params(self):
    raise NotImplementedError

  def _log_dataset(self, name):
    raise NotImplementedError

  def _set_parameters(self, parameters):
    raise NotImplementedError

  def _log_failure(self):
    raise NotImplementedError

  def _log_metadata(self, metadata):
    raise NotImplementedError

  def _log_sys_metadata(self, metadata):
    raise NotImplementedError

  def _log_dev_metadata(self, metadata):
    raise NotImplementedError

  def _log_metrics(self, metrics):
    raise NotImplementedError

  def _log_model(self, type):
    raise NotImplementedError

  def _log_source_code(self, source_code):
    raise NotImplementedError

  def _set_logs(self, logs):
    raise NotImplementedError

  def _log_checkpoint(self, values):
    raise NotImplementedError

  def _log_image(self, name, payload):
    raise NotImplementedError

  def _end(self, exception):
    raise NotImplementedError

  def set_parameter(self, name, value):
    '''
    sigopt.set_parameter(name, value)
    name: string, required
      The name of the parameter.
    value: number/string, required
      The value of the parameter.
    '''
    return self._set_parameters({name: value})

  def set_parameter_meta(self, name, value):
    return self._set_parameters_meta({name: value})

  def set_parameters_meta(self, parameters_meta):
    return self._set_parameters_meta(parameters_meta)

  def set_parameter_source(self, name, source):
    return self._set_parameters_meta({name: {"source": source}})

  def set_parameters_source(self, parameters, source):
    return self._set_parameters_meta({key: {"source": source} for key in parameters.keys()})

  def set_parameters_sources_meta(self, source_name, sort, default_show):
    return self._set_parameters_sources({source_name: {"sort": sort, "default_show": default_show}})

  def set_parameters(self, parameters):
    '''
    sigopt.set_parameter(parameters)
    name: dict, required
      A mapping of parameter names to values.
    '''
    return self._set_parameters(parameters)

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


  def log_dev_metadata(self, key, value):
    validate_name('metadata key', key)
    if value is not None and not isinstance(value, str):
      try:
        value = sanitize_number('metadata', key, value)
      except ValueError:
        value = str(value)
    return self._log_dev_metadata({key: value})


  def log_sys_metadata(self, key, value, mode=None):
    validate_name('metadata key', key)
    if mode == 'metadata':
      return self.log_metadata(key, value)
    elif mode == 'dev':
      return self.log_dev_metadata(key, value)
    return self._log_sys_metadata({key: value})

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

  def log_metrics(self, *args, **metric_kwargs):
    '''
    sigopt.log_metrics(metrics_dict)
    sigopt.log_metrics(**metric_kwargs)
      Logs multiple metric values for your run. Metrics can be provided as a dictionary or as keyword arguments.
    metrics_dict: dict
      A dictionary mapping metric names to their values.
    '''
    all_metrics = dict()
    all_metrics.update(*args, **metric_kwargs)
    metric_logs = {}
    for name, value in all_metrics.items():
      validate_name('metric name', name)
      metric_logs[name] = {"value": sanitize_number("metric", name, value)}
    self._log_metrics(metric_logs)

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

  def set_logs(self, logs):
    if not is_mapping(logs):
      raise TypeError(f"logs must be a mapping, got {type(logs).__name__}")
    for stream_name, stream_content in logs.items():
      validate_name("log stream", stream_name)
      if not is_string(stream_content):
        raise TypeError(f"log content must be a string, got {type(logs).__name__}")
    self._set_logs(logs)

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
    image_data = payload[1]
    with image_data:
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
    self._end(exception=exception)


def updates(update_key):

  def function_wrapper(wrapped_function):

    def function_impl(self, *args, **kwargs):
      update_value = wrapped_function(self, *args, **kwargs)
      self._update_run({update_key: update_value})

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
    default_params=None
  ):
    super().__init__()
    self.connection = connection
    self.run = run
    fixed_values = dict(run.assignments)
    self._params = RunParameters(self, fixed_values, default_params)

  def to_json(self):
    data = {"run": self.run.to_json()}
    return data

  @classmethod
  def from_json(cls, data):
    run = TrainingRun(data["run"])
    return cls(get_connection(), run)

  @property
  def id(self):
    return self.run.id

  @property
  def experiment(self):
    return self.run.experiment

  @property
  def params(self):
    return self._params

  def __enter__(self):
    return self

  def __exit__(self, type, value, tb):
    self._end(exception=value)

  def _end(self, exception):
    old_run_state = self.connection.training_runs(self.run.id).fetch().state
    new_run_state = 'failed' if exception else 'completed'
    if allow_state_update(new_run_state, old_run_state):
      self._update_run({'state': new_run_state})
    print_logger.info("Run finished, view it on the SigOpt dashboard at https://app.sigopt.com/run/%s", self.id)

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

  @updates('assignments')
  def _set_parameters(self, parameters):
    return parameters

  @updates('assignments_meta')
  def _set_parameters_meta(self, parameters_meta):
    return parameters_meta

  @updates('assignments_sources')
  def _set_parameters_sources(self, assignments_sources):
    return assignments_sources

  @updates('datasets')
  def _log_dataset(self, name):
    return {name: {}}

  @updates('state')
  def _log_failure(self):
    return 'failed'

  @updates('metadata')
  def _log_metadata(self, metadata):
    return metadata

  @updates('sys_metadata')
  def _log_sys_metadata(self, metadata):
    return metadata

  @updates('dev_metadata')
  def _log_dev_metadata(self, metadata):
    return metadata

  @updates('values')
  def _log_metrics(self, metrics):
    return metrics

  @updates('model')
  def _log_model(self, type):
    return remove_nones({'type': type})

  @updates('source_code')
  def _log_source_code(self, source_code):
    return source_code

  @updates('logs')
  def _set_logs(self, logs):
    return {
      name: {"content": maybe_truncate_log(content)}
      for name, content in logs.items()
    }

  @creates_checkpoint()
  def _log_checkpoint(self, values):
    return values

  def _log_image(self, name, payload):
    filename, image_data, content_type = payload
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
    self._params = GlobalRunParameters(self)

  @property
  def id(self):
    if self._run_context is None:
      return None
    return self._run_context.id

  @property
  def params(self):
    return self._params

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


for _method_name in [
  "_log_dataset",
  "_log_failure",
  "_log_metadata",
  "_log_sys_metadata",
  "_log_dev_metadata",
  "_log_metrics",
  "_log_model",
  "_log_checkpoint",
  "_log_image",
  "_set_parameters",
]:
  delegate_to_run_context(_method_name)

global_run_context = GlobalRunContext.from_config(config)
