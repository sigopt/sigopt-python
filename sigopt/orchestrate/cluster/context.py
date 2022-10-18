# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from .errors import NotConnectedError


class DisconnectOnException(object):
  def __init__(self, cluster_name, services):
    self._cluster_name = cluster_name
    self._services = services

  def __enter__(self):
    pass

  def __exit__(self, t, exc, tb):
    if exc is not None:
      try:
        self._services.cluster_service.disconnect(cluster_name=self._cluster_name, disconnect_all=False)
      except NotConnectedError:
        pass
      return False
    return None
