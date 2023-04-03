# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
# pylint: disable=unused-import

try:
  import json
except ImportError:
  try:
    import simplejson as json
  except ImportError as ie:
    raise ImportError(
      "No json library installed. Try running `pip install simplejson` to install a compatible json library."
    ) from ie
