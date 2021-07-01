from ..services.base import Service


class ProviderInterface(Service):
  def create_kubernetes_cluster(self, options):
    raise NotImplementedError()

  def destroy_kubernetes_cluster(self, cluster_name):
    raise NotImplementedError()

  def create_kubeconfig(self, cluster_name, ignore_role=False):
    raise NotImplementedError()

  def test_kubernetes_cluster(self, cluster_name, ignore_role=False):
    raise NotImplementedError()

  def create_cluster_object(self, services, name, registry):
    raise NotImplementedError()
