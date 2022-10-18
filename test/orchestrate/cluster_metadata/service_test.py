# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import pytest
from mock import Mock

from sigopt.orchestrate.common import TemporaryDirectory
from sigopt.orchestrate.cluster.object import AWSCluster
from sigopt.orchestrate.cluster_metadata.errors import *
from sigopt.orchestrate.cluster_metadata.service import ClusterMetadataService
from sigopt.orchestrate.custom_cluster.service import CustomClusterService
from sigopt.orchestrate.provider.constants import Provider


# pylint: disable=protected-access

class TestClusterService(object):
  @pytest.fixture
  def services(self):
    mock_services = Mock()

    def fake_create_cluster_object(services, name, registry):
      return AWSCluster(
        services=services,
        name=name,
        registry=registry,
      )

    def fake_get_provider_service(provider):
      if provider == Provider.AWS:
        return Mock(
          create_cluster_object=fake_create_cluster_object
        )
      elif provider == Provider.CUSTOM:
        return CustomClusterService(mock_services)
      else:
        raise NotImplementedError()

    mock_services.provider_broker.get_provider_service = fake_get_provider_service
    return mock_services

  @pytest.fixture
  def cluster_metadata_service(self, services):
    cluster_metadata_service = ClusterMetadataService(services)
    services.cluster_metadata_service = cluster_metadata_service
    return cluster_metadata_service

  @pytest.mark.parametrize('provider', [
    Provider.AWS,
    Provider.CUSTOM,
  ])
  def test_custom_cluster(self, cluster_metadata_service, provider):
    with TemporaryDirectory() as root_dirname:
      cluster_metadata_service._metadata_dir = root_dirname

      provider_service = cluster_metadata_service.services.provider_broker.get_provider_service(provider)
      cluster = provider_service.create_cluster_object(
        services=cluster_metadata_service.services,
        name='foobar',
        registry=None,
      )
      cluster_metadata_service.write_metadata(cluster)

      cluster = cluster_metadata_service.read_metadata('foobar')
      assert cluster.name == 'foobar'
      assert cluster.provider == provider

  def test_double_write(self, cluster_metadata_service):
    with TemporaryDirectory() as root_dirname:
      cluster_metadata_service._metadata_dir = root_dirname

      custom_cluster_service = cluster_metadata_service.services.provider_broker.get_provider_service(Provider.CUSTOM)
      cluster = custom_cluster_service.create_cluster_object(
        services=cluster_metadata_service.services,
        name='foobar',
        registry=None,
      )
      cluster_metadata_service.write_metadata(cluster)

      with pytest.raises(MetadataAlreadyExistsError):
        cluster_metadata_service.write_metadata(cluster)

  def test_no_metadata(self, cluster_metadata_service):
    with TemporaryDirectory() as root_dirname:
      cluster_metadata_service._metadata_dir = root_dirname

      with pytest.raises(Exception):
        cluster_metadata_service.read_metadata('foobar')
