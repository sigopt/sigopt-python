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
    if global_failed_status_count > self.limit:
      time.sleep(random.random() * 2)

  def clear(self):
    with thread_lock:
      global global_failed_status_count
      global_failed_status_count = 0
