# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT


def batcher(alist, n=1):
  l = len(alist)
  for ndx in range(0, l, n):
    yield alist[ndx : min(ndx + n, l)]
