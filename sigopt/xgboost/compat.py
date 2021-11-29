# pylint: disable=unused-import
MIN_REQUIRED_XGBOOST_VERSION = "1.3.0"


try:
  import xgboost
  from xgboost import Booster, DMatrix
except ImportError as ie_xgb:
  raise ImportError(
    "xgboost needs to be installed in order to use sigopt.xgboost.run functionality. "
    "Try running `pip install sigopt [xgboost]`."
  ) from ie_xgb


try:
  from packaging.version import parse
except ImportError as ie_packaging:
  satisfies_xgb_req = True
  installed_xgb_ver = xgboost.__version__.split(".")
  required_xgb_ver = MIN_REQUIRED_XGBOOST_VERSION.split(".")

  if installed_xgb_ver[0] < required_xgb_ver[0]:
    satisfies_xgb_req = False
  elif installed_xgb_ver[1] < required_xgb_ver[1]:
    satisfies_xgb_req = False

  if not satisfies_xgb_req:
    raise ImportError(
      f"sigopt.xgboost.run is compatible with xgboost>={MIN_REQUIRED_XGBOOST_VERSION}. "
      f"You have version {xgboost.__version__} installed."
    ) from None

if parse(xgboost.__version__) < parse(MIN_REQUIRED_XGBOOST_VERSION):
  raise ImportError(
    f"sigopt.xgboost.run is compatible with xgboost>={MIN_REQUIRED_XGBOOST_VERSION}. "
    f"You have version {xgboost.__version__} installed."
  )
