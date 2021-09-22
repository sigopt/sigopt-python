import random
import threading
import time


global_failed_status_count = 0
thread_lock = threading.Lock()

class FailedStatusRateLimit(object):
  def __init__(self, limit):
    self.limit = limit

  def increment_and_check(self):
    with thread_lock:
      global global_failed_status_count
      global_failed_status_count += 1

    multiples_over = global_failed_status_count // self.limit
    if multiples_over:
      exponential_backoff = multiples_over ** 2
      jitter = random.random() * 2
      time.sleep(exponential_backoff + jitter)

  def clear(self):
    with thread_lock:
      global global_failed_status_count
      global_failed_status_count = 0
