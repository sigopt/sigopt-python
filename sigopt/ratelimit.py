# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import secrets
import threading
import time


class _FailedStatusRateLimit(object):
  def __init__(self, limit):
    self.limit = limit
    self.thread_lock = threading.Lock()
    self.count = 0

  def increment_and_check(self):
    with self.thread_lock:
      self.count += 1
      multiples_over = self.count // self.limit
    if multiples_over:
      quadratic_backoff = multiples_over**2
      jitter = secrets.SystemRandom().random() * 2
      time.sleep(quadratic_backoff + jitter)

  def clear(self):
    with self.thread_lock:
      self.count = 0


failed_status_rate_limit = _FailedStatusRateLimit(5)
