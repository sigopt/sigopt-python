# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import math


# Franke function - http://www.sfu.ca/~ssurjano/franke2d.html
def franke_function(x1, x2):
  return (
    0.75 * math.exp(-((9 * x1 - 2) ** 2) / 4.0 - (9 * x2 - 2) ** 2 / 4.0)
    + 0.75 * math.exp(-((9 * x1 + 1) ** 2) / 49.0 - (9 * x2 + 1) / 10.0)
    + 0.5 * math.exp(-((9 * x1 - 7) ** 2) / 4.0 - (9 * x2 - 3) ** 2 / 4.0)
    - 0.2 * math.exp(-((9 * x1 - 4) ** 2) - (9 * x2 - 7) ** 2)
  )


# Create a SigOpt experiment that optimized the Franke function with
# connection.experiments().create(**FRANKE_EXPERIMENT_DEFINITION)
FRANKE_EXPERIMENT_DEFINITION = {
  "name": "Franke Optimization",
  "parameters": [
    {"name": "x", "bounds": {"max": 1, "min": 0}, "type": "double", "precision": 4},
    {"name": "y", "bounds": {"max": 1, "min": 0}, "type": "double", "precision": 4},
  ],
}
