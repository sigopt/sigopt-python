import warnings

from .config import config
from .defaults import get_default_project
from .interface import Connection, get_connection
from .logging import enable_print_logging
from .magics import SigOptMagics as _Magics
from .run_context import global_run_context as _global_run_context, RunContext
from .factory import SigOptFactory
from .version import VERSION


params = _global_run_context.params
log_checkpoint = _global_run_context.log_checkpoint
log_dataset = _global_run_context.log_dataset
log_failure = _global_run_context.log_failure
log_image = _global_run_context.log_image
log_metadata = _global_run_context.log_metadata
log_metric = _global_run_context.log_metric
log_metrics = _global_run_context.log_metrics
log_model = _global_run_context.log_model
log_sys_metadata = _global_run_context.log_sys_metadata
config.set_context_entry(_global_run_context)

_global_factory = SigOptFactory(get_default_project())
create_run = _global_factory.create_run
create_experiment = _global_factory.create_experiment
get_experiment = _global_factory.get_experiment
archive_experiment = _global_factory.archive_experiment
unarchive_experiment = _global_factory.unarchive_experiment
archive_run = _global_factory.archive_run
unarchive_run = _global_factory.unarchive_run
get_run = _global_factory.get_run


def load_ipython_extension(ipython):
  ipython.register_magics(_Magics)
  enable_print_logging()

def get_run_id():
  return _global_run_context.id

def set_project(project):
  if get_run_id() is not None:
    warnings.warn(
      "set_project does nothing when your code is executed with the SigOpt CLI."
      " Set the SIGOPT_PROJECT environment variable or use the --project CLI option instead.",
      UserWarning,
    )
  return _global_factory.set_project(project)

def switch_run_context(run_id):
  if get_run_id() == run_id:
    return

  context = RunContext(
    connection = get_connection(),
    run = get_run(run_id))
  _global_run_context._run_context = context
