import random
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
    with self.thread_lock:
      multiples_over = self.count // self.limit
    if multiples_over:
      exponential_backoff = multiples_over ** 2
      jitter = random.random() * 2
      time.sleep(exponential_backoff + jitter)

  def clear(self):
    with self.thread_lock:
      self.count = 0

failed_status_rate_limit = _FailedStatusRateLimit(5)
