# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from ..exceptions import OrchestrateException
from ..version import CLI_NAME


class ClusterError(OrchestrateException):
  pass


class MultipleClustersConnectionError(ClusterError):
  def __init__(self, connected_clusters):
    safe_str = "\n\t".join(connected_clusters)
    super().__init__(
      "You are currently connected to more than one cluster, all of which are listed below."
      "\nPlease disconnect from some of these clusters before re-running your command."
      "\nConnected clusters:"
      f":\n\t{safe_str}"
    )
    self.connected_clusters = connected_clusters


class PleaseDisconnectError(ClusterError):
  def __init__(self, current_cluster_name):
    super().__init__(
      f"Please disconnect from this cluster before re-running your command: {current_cluster_name}"
    )
    self.current_cluster_name = current_cluster_name


class NotConnectedError(ClusterError):
  def __init__(self):
    super().__init__("You are not currently connected to any cluster")


class AlreadyConnectedException(ClusterError):
  def __init__(self, current_cluster_name):
    super().__init__(
      f"You are already connected this cluster: {current_cluster_name}."
      f" Please run `{CLI_NAME} cluster test` to verify the details of your connection.",
    )
    self.current_cluster_name = current_cluster_name
