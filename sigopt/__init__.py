from .interface import Connection
from .magics import SigOptMagics as _Magics
from .runs import (
  set_parameters,
  get_parameter,
  log_checkpoint,
  log_dataset,
  log_metadata,
  log_metric,
  log_model,
  log_failure,
  log_image,
  create_run,
)
from .version import VERSION


def load_ipython_extension(ipython):
  ipython.register_magics(_Magics)
