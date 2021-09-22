import datetime
import random
import time


class RateLimit(object):
  def __init__(self, limit, key=None):
    self.limit = limit
    self.key = key
    self.count = 0

  @staticmethod
  def _datetime_to_seconds(dt):
    return int((dt - datetime.datetime(1970, 1, 1)).total_seconds())

  @staticmethod
  def now():
    return RateLimit._datetime_to_seconds(datetime.datetime.now())

  def increment_and_check(self, value=None):
    if self.key is not None:
      if value != self.key:
        self.key = value
        self.count = 0
    self.count += 1
    if self.count > self.limit:
      time.sleep(random.random() * 2)

  def clear(self):
    self.count = 0
