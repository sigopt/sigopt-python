# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from ..cluster.object import CustomCluster
from ..exceptions import OrchestrateException
from ..provider.constants import Provider, provider_to_string
from ..provider.interface import ProviderInterface
from ..version import CLI_NAME


class CustomClusterService(ProviderInterface):
  def create_kubernetes_cluster(self, options):
    cluster_name = options.get("cluster_name", "my-cluster")
    raise OrchestrateException(
      f'When you use provider = "{provider_to_string(Provider.CUSTOM)}", we'
      " assume that you have created your own kubernetes cluster. If you are"
      " attempting to connect to a custom cluster that you have already created,"
      f" please use:\n{CLI_NAME} cluster connect --provider custom --kubeconfig"
      f" <kubeconfig> --cluster-name {cluster_name}"
    )

  def destroy_kubernetes_cluster(self, cluster_name):
    raise OrchestrateException(
      f'When you use provider = "{provider_to_string(Provider.CUSTOM)}", we'
      " assume that you have created your own kubernetes cluster. If you are"
      " attempting to disconnect from a custom cluster that you have already"
      f" created, please use:\n{CLI_NAME} cluster disconnect --cluster-name"
      f" {cluster_name}"
    )

  def create_kubeconfig(self, cluster_name, ignore_role=False):
    raise OrchestrateException(
      f'When you use provider = "{provider_to_string(Provider.CUSTOM)}", we'
      " assume that you have created your own kubernetes cluster. Additionally"
      " we assume that you have a copy of the kubeconfig file that is used to"
      " access the cluster. Please provide the path to the kubeconfig as an"
      " argument. You will also need to provide the URL for your container"
      f" registry, if using a private one.\n{CLI_NAME} cluster connect --provider"
      " custom --kubeconfig <kubeconfig> --cluster-name"
      f" {cluster_name} [--registry <registry-url>]"
    )

  def test_kubernetes_cluster(self, cluster_name, ignore_role=False):
    self.services.kubernetes_service.test_config()

  def create_cluster_object(self, services, name, registry):
    return CustomCluster(
      services=services,
      name=name,
      registry=registry,
    )
