# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import pytest

import sigopt


class TestSigOpt(object):
  def create_run(self, n):
    return {
      "name": f"batch-{n}",
      "assignments": {
        "x": n,
        "y": n * n,
      },
      "values": {
        "r0": dict(value=n * n + n),
        "r1": dict(value=n**2),
      },
      "state": "completed" if (n % 2 == 0) else "failed",
    }

  @pytest.mark.parametrize("n", [10, 11])
  @pytest.mark.parametrize("max_batch_size", [2, 3, 10, 20])
  def test_upload_runs(self, n, max_batch_size):
    runs = [self.create_run(i) for i in range(n)]
    training_runs = sigopt.upload_runs(runs, max_batch_size)
    assert len(training_runs) == n
