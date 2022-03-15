# pylint: disable=unused-import
from packaging.version import parse

MIN_REQUIRED_XGBOOST_VERSION = "1.3.0"

try:
  import xgboost
  from xgboost import Booster, DMatrix
  xgboost_train = xgboost.train

except ImportError as ie_xgb:
  raise ImportError(
    "xgboost needs to be installed in order to use sigopt.xgboost.run functionality. "
    "Try running `pip install 'sigopt[xgboost]'`."
  ) from ie_xgb

if parse(xgboost.__version__) < parse(MIN_REQUIRED_XGBOOST_VERSION):
  raise ImportError(
    f"sigopt.xgboost.run is compatible with xgboost>={MIN_REQUIRED_XGBOOST_VERSION}. "
    f"You have version {xgboost.__version__} installed."
  )
