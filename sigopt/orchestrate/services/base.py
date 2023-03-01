# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
class Service(object):
  """
  Base class for all services.
  """
  def __init__(self, services):
    self.services = services
