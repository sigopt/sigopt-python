# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from ..services.base import Service


class AwsService(Service):
  """
  Base class for all AWS services.
  """
  def __init__(self, services, aws_services):
    super().__init__(services)
    self.aws_services = aws_services
