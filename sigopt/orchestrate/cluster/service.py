from ..provider.constants import Provider, string_to_provider
from ..services.base import Service
from .context import DisconnectOnException
from .errors import (
  AlreadyConnectedException,
  ClusterError,
  MultipleClustersConnectionError,
  NotConnectedError,
  PleaseDisconnectError,
)


class ClusterService(Service):
  def connected_clusters(self):
    return self.services.kubernetes_service.get_cluster_names()

  def assert_is_connected(self):
    connected_clusters = self.connected_clusters()
    if not connected_clusters:
      raise NotConnectedError()
    if len(connected_clusters) > 1:
      raise MultipleClustersConnectionError(connected_clusters)
    return connected_clusters[0]

  def assert_is_disconnected(self):
    connected_clusters = self.connected_clusters()
    if connected_clusters:
      if len(connected_clusters) == 1:
        raise PleaseDisconnectError(connected_clusters[0])
      raise MultipleClustersConnectionError(connected_clusters)

  def connect(self, cluster_name, provider_string, kubeconfig, registry):
    try:
      self.assert_is_disconnected()
    except PleaseDisconnectError as e:
      if e.current_cluster_name == cluster_name:
        raise AlreadyConnectedException(e.current_cluster_name) from e
      raise

    provider = string_to_provider(provider_string)
    provider_service = self.services.provider_broker.get_provider_service(provider)

    if kubeconfig is None:
      kubeconfig = provider_service.create_kubeconfig(cluster_name)
    else:
      assert provider == Provider.CUSTOM, "Must use --provider custom to connect with a kubeconfig"

    with DisconnectOnException(cluster_name, self.services):
      self.services.kubernetes_service.write_config(cluster_name, kubeconfig)
      self.services.kubernetes_service.ensure_orchestrate_namespace()
      cluster = provider_service.create_cluster_object(
        services=self.services,
        name=cluster_name,
        registry=registry,
      )
      self.services.cluster_metadata_service.write_metadata(cluster)
      return self.test()

  def create(self, options):
    try:
      self.assert_is_disconnected()
    except PleaseDisconnectError as e:
      if e.current_cluster_name == options.get('cluster_name', ''):
        raise AlreadyConnectedException(e.current_cluster_name) from e
      raise

    self.services.options_validator_service.validate_cluster_options(**options)
    cluster_name = options.get('cluster_name', '')

    provider_string = options.get('provider', '')
    provider = string_to_provider(provider_string)
    provider_service = self.services.provider_broker.get_provider_service(provider)

    with DisconnectOnException(cluster_name, self.services):
      cluster = provider_service.create_kubernetes_cluster(options)
      self.services.kubernetes_service.ensure_orchestrate_namespace()
      self.services.cluster_metadata_service.write_metadata(cluster)
      self.services.kubernetes_service.wait_until_nodes_are_ready()
      return cluster.name

  def update(self, options):
    self.services.options_validator_service.validate_cluster_options(**options)
    cluster_name = options.get('cluster_name', '')

    provider_string = options.get('provider', '')
    provider = string_to_provider(provider_string)
    provider_service = self.services.provider_broker.get_provider_service(provider)

    with DisconnectOnException(cluster_name, self.services):
      cluster = provider_service.update_kubernetes_cluster(options)
      self.services.kubernetes_service.ensure_orchestrate_namespace()
      self.services.kubernetes_service.wait_until_nodes_are_ready()
      return cluster.name

  def destroy(self, cluster_name, provider_string):
    provider = string_to_provider(provider_string)
    provider_service = self.services.provider_broker.get_provider_service(provider)
    provider_service.destroy_kubernetes_cluster(cluster_name=cluster_name)
    self.services.cluster_metadata_service.ensure_metadata_deleted(cluster_name=cluster_name)

  def disconnect(self, cluster_name, disconnect_all):
    if (cluster_name and disconnect_all) or (not cluster_name and not disconnect_all):
      raise ClusterError('Must provide exactly one of --cluster-name <cluster_name> and --all')

    try:
      current_cluster_name = self.assert_is_connected()
      if cluster_name is not None and current_cluster_name != cluster_name:
        raise PleaseDisconnectError(current_cluster_name)
    except MultipleClustersConnectionError:
      if not disconnect_all:
        raise

    for cname in self.connected_clusters():
      try:
        self.services.cluster_metadata_service.ensure_metadata_deleted(cluster_name=cname)
        self.services.kubernetes_service.ensure_config_deleted(cluster_name=cname)
        self.services.logging_service.warning(f'Successfully disconnected from {cname}')
      except Exception as e:
        raise ClusterError(
          f'Looks like an error occured while attempting to disconnect from cluster "{cname}".'
        ) from e

  def get_connected_cluster(self):
    cluster_name = self.assert_is_connected()
    return self.services.cluster_metadata_service.read_metadata(cluster_name)

  def test(self):
    cluster = self.get_connected_cluster()
    provider_service = self.services.provider_broker.get_provider_service(cluster.provider)

    try:
      provider_service.test_kubernetes_cluster(cluster_name=cluster.name)
    except Exception as e:
      raise ClusterError(
        f'Looks like an error occured while testing cluster "{cluster.name}".'
      ) from e

    return cluster
