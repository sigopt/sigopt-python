# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from ..exceptions import OrchestrateException


class MetadataError(OrchestrateException):
  def __init__(self, cluster_name, unformatted_msg):
    formatted_msg = unformatted_msg.format(cluster_name=cluster_name)
    super().__init__(
      f"{formatted_msg} Disconnecting and then reconnecting should resolve the issue.",
    )
    self.cluster_name = cluster_name


class MetadataNotFoundError(MetadataError):
  def __init__(self, cluster_name):
    super().__init__(
      cluster_name,
      f"We could not find metadata for cluster {cluster_name}.",
    )


class MetadataAlreadyExistsError(MetadataError):
  def __init__(self, cluster_name):
    super().__init__(
      cluster_name,
      f"Looks like metadata for cluster {cluster_name} already exists.",
    )
