# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import pytest
from mock import Mock

from sigopt.orchestrate.cluster.errors import (
  AlreadyConnectedException,
  MultipleClustersConnectionError,
  NotConnectedError,
  PleaseDisconnectError,
)
from sigopt.orchestrate.cluster.object import AWSCluster, CustomCluster
from sigopt.orchestrate.cluster.service import ClusterService
from sigopt.orchestrate.custom_cluster.service import CustomClusterService
from sigopt.orchestrate.exceptions import OrchestrateException
from sigopt.orchestrate.provider.constants import Provider


class TestClusterService(object):
  @pytest.fixture
  def services(self):
    mock_services = Mock()
    mock_services.get_option = Mock(return_value='bar')

    def fake_get_provider_service(provider):
      if provider == Provider.AWS:
        return Mock(
          create_kubernetes_cluster=Mock(return_value=AWSCluster(
            services=mock_services,
            name='foobar',
            registry=None,
          ))
        )
      elif provider == Provider.CUSTOM:
        return CustomClusterService(mock_services)
      else:
        raise NotImplementedError()

    mock_services.provider_broker.get_provider_service = fake_get_provider_service
    return mock_services

  @pytest.fixture
  def cluster_service(self, services):
    cluster_service = ClusterService(services)
    services.cluster_service = cluster_service
    return cluster_service

  def test_connected_clusters(self, cluster_service):
    cluster_service.services.kubernetes_service.get_cluster_names.return_value = []
    assert cluster_service.connected_clusters() == []
    cluster_service.services.kubernetes_service.get_cluster_names.return_value = ['foo']
    assert cluster_service.connected_clusters() == ['foo']
    cluster_service.services.kubernetes_service.get_cluster_names.return_value = ['foo', 'bar']
    assert sorted(cluster_service.connected_clusters()) == ['bar', 'foo']

  def test_multiple_clusters(self, cluster_service):
    cluster_service.connected_clusters = Mock(return_value=['bar', 'foo'])

    with pytest.raises(MultipleClustersConnectionError):
      cluster_service.assert_is_connected()
    with pytest.raises(MultipleClustersConnectionError):
      cluster_service.assert_is_disconnected()
    with pytest.raises(MultipleClustersConnectionError):
      cluster_service.connect(
        cluster_name=None,
        provider_string='aws',
        kubeconfig=None,
        registry=None,
      )
    with pytest.raises(MultipleClustersConnectionError):
      cluster_service.create(None)
    with pytest.raises(MultipleClustersConnectionError):
      cluster_service.disconnect('bar', None)
    with pytest.raises(MultipleClustersConnectionError):
      cluster_service.test()

    cluster_service.disconnect(cluster_name=None, disconnect_all=True)

    # TODO(alexandra): decide which permissions to validate for cluster destroy
    cluster_service.destroy(None, 'aws')

  def test_no_clusters(self, cluster_service):
    cluster_service.connected_clusters = Mock(return_value=[])

    with pytest.raises(NotConnectedError):
      cluster_service.assert_is_connected()
    with pytest.raises(NotConnectedError):
      cluster_service.disconnect('bar', None)
    with pytest.raises(NotConnectedError):
      cluster_service.disconnect(cluster_name=None, disconnect_all=True)
    with pytest.raises(NotConnectedError):
      cluster_service.test()

    cluster_service.assert_is_disconnected()
    cluster_service.test = Mock()
    cluster_service.connect(
      cluster_name='cluster_name',
      provider_string='aws',
      kubeconfig=None,
      registry=None,
    )
    assert cluster_service.test.call_count == 1
    cluster_service.create(dict(provider='aws'))

    # TODO(alexandra): decide which permissions to validate for cluster destroy
    cluster_service.destroy(None, 'aws')

  def test_one_clusters(self, cluster_service):
    cluster_service.connected_clusters = Mock(return_value=['foo'])
    cluster_service.services.cluster_metadata_service.read_metadata = Mock(
      return_value=CustomCluster(
        services=cluster_service.services,
        name='foo',
        registry=None,
      )
    )

    with pytest.raises(PleaseDisconnectError):
      cluster_service.assert_is_disconnected()
    with pytest.raises(PleaseDisconnectError):
      cluster_service.connect(
        cluster_name='bar',
        provider_string='aws',
        kubeconfig=None,
        registry=None,
      )
    with pytest.raises(PleaseDisconnectError):
      cluster_service.create(dict(cluster_name='bar'))
    with pytest.raises(PleaseDisconnectError):
      cluster_service.disconnect('bar', None)

    cluster_service.assert_is_connected()

    with pytest.raises(AlreadyConnectedException):
      cluster_service.connect(
        cluster_name='foo',
        provider_string='aws',
        kubeconfig=None,
        registry=None,
      )
    with pytest.raises(AlreadyConnectedException):
      cluster_service.create(dict(cluster_name='foo'))

    cluster_service.disconnect('foo', None)
    cluster_service.disconnect(cluster_name=None, disconnect_all=True)
    cluster_service.destroy('foo', 'aws')
    cluster_service.test()

    # TODO(alexandra): decide which permissions to validate for cluster destroy
    cluster_service.destroy('bar', 'aws')

  def test_create_cluster(self, cluster_service):
    cluster_service.connected_clusters = Mock(return_value=[])
    cluster_name = cluster_service.create(dict(provider='aws'))
    assert cluster_name == 'foobar'

  def test_create_cluster_fails(self, cluster_service):
    # Mock this function so that cluster create things that we are not connected, and will try to creat a cluster
    cluster_service.assert_is_disconnected = Mock()
    # Mock this function so that cluster disconnect will think that we are connected to foobar
    cluster_service.connected_clusters = Mock(return_value=['foobar'])

    exc = Exception()
    cluster_service.services.provider_broker.get_provider_service = Mock(
      return_value=Mock(
        create_kubernetes_cluster=Mock(side_effect=exc),
      ),
    )
    with pytest.raises(Exception) as e:
      cluster_service.create(dict(cluster_name='foobar', provider='aws'))
    assert e.value is exc
    cluster_service.services.kubernetes_service.ensure_config_deleted.assert_called_with(cluster_name='foobar')

  def test_cluster_test(self, cluster_service):
    cluster_service.connected_clusters = Mock(return_value=['foobar'])
    cluster_service.services.cluster_metadata_service.read_metadata = Mock(
      return_value=CustomCluster(
        services=cluster_service.services,
        name='foobar',
        registry=None,
      )
    )

    cluster = cluster_service.test()
    assert cluster.name == 'foobar'
    assert cluster.provider_string == 'custom'

    cluster_service.connected_clusters = Mock(return_value=['bar'])
    cluster_service.services.cluster_metadata_service.read_metadata = Mock(
      return_value=AWSCluster(
        services=cluster_service.services,
        name='bar',
        registry=None,
      )
    )

    cluster = cluster_service.test()
    assert cluster.name == 'bar'
    assert cluster.provider_string == 'aws'

  def test_cluster_connect(self, cluster_service):
    cluster_service.connected_clusters = Mock(return_value=[])
    cluster_service.test = Mock()
    cluster_service.connect(
      cluster_name='bar',
      provider_string='custom',
      kubeconfig='foo',
      registry=None,
    )

    cluster_service.connect(
      cluster_name='bar',
      provider_string='aws',
      kubeconfig=None,
      registry=None,
    )

    with pytest.raises(AssertionError):
      cluster_service.connect(
        cluster_name='bar',
        provider_string='aws',
        kubeconfig='foo',
        registry=None,
      )

    with pytest.raises(OrchestrateException):
      cluster_service.connect(
        cluster_name='bar',
        provider_string='custom',
        kubeconfig=None,
        registry=None,
      )
