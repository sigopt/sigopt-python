# pylint: disable=unused-import
from packaging.version import parse

MIN_REQUIRED_HYPEROPT_VERSION = "0.2.7"

try:
  import hyperopt
  from hyperopt import Trials, STATUS_OK, STATUS_FAIL, fmin

except ImportError as ie_xgb:
  raise ImportError(
    "hyperopt needs to be installed in order to use sigopt.hyperopt.run functionality. "
    "Try running `pip install 'sigopt[hyperopt]'`."
  ) from ie_xgb

if parse(hyperopt.__version__) < parse(MIN_REQUIRED_HYPEROPT_VERSION):
  raise ImportError(
    f"sigopt.hyperopt is compatible with hyperopt>={MIN_REQUIRED_HYPEROPT_VERSION}. "
    f"You have version {hyperopt.__version__} installed."
  )
