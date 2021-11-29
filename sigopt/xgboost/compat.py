# pylint: disable=unused-import

try:
  import xgboost
  from xgboost import Booster, DMatrix
except ImportError as ie_xgb:
  raise ImportError(
    "xgboost needs to be installed in order to use sigopt.xgboost.run functionality. "
    "Try running `pip install sigopt [xgboost]`."
  ) from ie_xgb
