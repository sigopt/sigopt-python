# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import errno
import os

import yaml
from sigopt.paths import ensure_dir, get_root_subdir

from ..provider.constants import string_to_provider
from ..services.base import Service
from .errors import MetadataAlreadyExistsError, MetadataNotFoundError


class ClusterMetadataService(Service):
  def __init__(self, services):
    super().__init__(services)
    self._metadata_dir = get_root_subdir('cluster')

  def read_metadata(self, cluster_name):
    metadata_path = self._cluster_metadata_path(cluster_name)

    if not os.path.isfile(metadata_path):
      raise MetadataNotFoundError(cluster_name)

    with open(metadata_path, 'r') as f:
      data = yaml.safe_load(stream=f)

    provider = string_to_provider(data['provider'])
    provider_service = self.services.provider_broker.get_provider_service(provider)
    cluster = provider_service.create_cluster_object(
      services=self.services,
      name=data['name'],
      registry=data['registry'],
    )
    return cluster

  def write_metadata(self, cluster):
    data = dict(
      name=cluster.name,
      provider=cluster.provider_string,
      registry=cluster.registry,
    )

    ensure_dir(self._metadata_dir)
    metadata_path = self._cluster_metadata_path(cluster.name)

    if os.path.isfile(metadata_path):
      raise MetadataAlreadyExistsError(cluster.name)

    with open(metadata_path, 'w') as f:
      yaml.safe_dump(data, stream=f)

  def _delete_metadata(self, cluster_name):
    try:
      os.remove(self._cluster_metadata_path(cluster_name))
    except OSError as e:
      if e.errno == errno.ENOENT:
        raise MetadataNotFoundError(cluster_name) from e
      raise

  def ensure_metadata_deleted(self, cluster_name):
    try:
      self._delete_metadata(cluster_name)
    except MetadataNotFoundError:
      pass

  def _cluster_metadata_path(self, cluster_name):
    filename = f'metadata-{cluster_name}'
    return os.path.join(self._metadata_dir, filename)
