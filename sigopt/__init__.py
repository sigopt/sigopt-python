from .interface import Connection
from .magics import SigOptMagics as _Magics
from .runs import (
  RunFactory,
  create_experiment,
  create_run,
  get_parameter,
  log_checkpoint,
  log_dataset,
  log_failure,
  log_image,
  log_metadata,
  log_metric,
  log_model,
  set_parameters,
)
from .version import VERSION


def load_ipython_extension(ipython):
  ipython.register_magics(_Magics)

def get_run_id():
  return RunFactory.get_global_run_context().run_id
