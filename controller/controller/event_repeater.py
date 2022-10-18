# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import threading


class EventRepeater:
  def __init__(self, period, event):
    self.period = period
    self.event = event
    self.timer = None

  def new_timer(self):
    self.timer = threading.Timer(self.period, self.repeat)
    self.timer.start()

  def start(self):
    self.new_timer()

  def repeat(self):
    self.event.set()
    self.new_timer()

  def cancel(self):
    self.timer.cancel()
