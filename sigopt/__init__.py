from .config import config
from .defaults import get_default_project
from .interface import Connection
from .magics import SigOptMagics as _Magics
from .run_context import GlobalRunContext as _GlobalRunContext
from .experiment_context import create_experiment
from .run_factory import RunFactory
from .version import VERSION


_global_run_context = _GlobalRunContext.from_config(config)
log_checkpoint = _global_run_context.log_checkpoint
log_dataset = _global_run_context.log_dataset
log_failure = _global_run_context.log_failure
log_image = _global_run_context.log_image
log_metadata = _global_run_context.log_metadata
log_metric = _global_run_context.log_metric
log_model = _global_run_context.log_model
config.set_context_entry(_global_run_context)

_global_run_factory = RunFactory(get_default_project())
create_run = _global_run_factory.create_run


def load_ipython_extension(ipython):
  ipython.register_magics(_Magics)

def get_run_id():
  global _global_run_context
  return _global_run_context.id
