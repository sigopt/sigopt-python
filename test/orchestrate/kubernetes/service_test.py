# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import pytest
from kubernetes import client
from mock import MagicMock, Mock, patch

from sigopt.orchestrate.exceptions import NodesNotReadyError
from sigopt.orchestrate.kubernetes.service import ORCHESTRATE_NAMESPACE, KubernetesService


# pylint: disable=protected-access
class TestKubernetesService(object):
  @pytest.fixture()
  def kubernetes_service(self):
    services = Mock()
    return KubernetesService(services)

  def test_delete_job(self, kubernetes_service):
    kubernetes_service._v1_batch = Mock()
    kubernetes_service.delete_job("test_job_name")

    kubernetes_service._v1_batch.delete_namespaced_job.assert_called_with(
      "test_job_name",
      ORCHESTRATE_NAMESPACE,
      body=client.V1DeleteOptions(),
    )

  def test_start_job(self, kubernetes_service):
    kubernetes_service._v1_batch = Mock()
    kubernetes_service.start_job("test_job_spec")

    kubernetes_service._v1_batch.create_namespaced_job.assert_called_with(ORCHESTRATE_NAMESPACE, "test_job_spec")

  def test_logs(self, kubernetes_service):
    kubernetes_service._v1_core = Mock()
    kubernetes_service.logs("foobar")

    kubernetes_service._v1_core.read_namespaced_pod_log.assert_called_with("foobar", ORCHESTRATE_NAMESPACE)

  def test_pod_names(self, kubernetes_service):
    foo_mock = Mock()
    foo_mock.metadata.name = "foo"
    bar_mock = Mock()
    bar_mock.metadata.name = "bar"

    get_pods_result = MagicMock()
    get_pods_result.items = [foo_mock, bar_mock]
    kubernetes_service.get_pods = Mock(return_value=get_pods_result)

    assert kubernetes_service.pod_names("baz") == ["foo", "bar"]
    kubernetes_service.get_pods.assert_called_with(job_name="baz")

  def test_get_pods(self, kubernetes_service):
    kubernetes_service._v1_core = Mock()
    kubernetes_service.get_pods()

    kubernetes_service._v1_core.list_namespaced_pod.assert_called_with(ORCHESTRATE_NAMESPACE, watch=False)

  def test_get_pods_with_job_name(self, kubernetes_service):
    kubernetes_service._v1_core = Mock()
    kubernetes_service.get_pods("test_job_name")

    kubernetes_service._v1_core.list_namespaced_pod.assert_called_with(
      ORCHESTRATE_NAMESPACE, watch=False, label_selector="job-name=test_job_name"
    )

  def test_wait_until_nodes_are_ready(self, kubernetes_service):
    with patch("sigopt.orchestrate.kubernetes.service.time") as mock_time:
      kubernetes_service.check_nodes_are_ready = Mock(
        side_effect=[
          NodesNotReadyError("not ready"),
          NodesNotReadyError("not ready"),
          NodesNotReadyError("not ready"),
          None,
          None,
        ]
      )
      kubernetes_service.wait_until_nodes_are_ready()
      assert kubernetes_service.check_nodes_are_ready.call_count == 4
      assert mock_time.sleep.called

  def test_check_nodes_are_ready(self, kubernetes_service):
    ready_true_cond = Mock(status="True", type="Ready")
    foobar_true_cond = Mock(status="True", type="foobar")
    foobar_false_cond = Mock(status="False", type="foobar")

    node_mock1 = Mock(status=Mock(conditions=[ready_true_cond, foobar_true_cond]))
    node_mock2 = Mock(status=Mock(conditions=[ready_true_cond, foobar_false_cond]))

    kubernetes_service.get_nodes = MagicMock()
    kubernetes_service.get_nodes().items = [node_mock1, node_mock2]

    kubernetes_service.check_nodes_are_ready()

  def test_check_nodes_are_not_ready_status(self, kubernetes_service):
    ready_false_cond = Mock(status="False", type="Ready")
    foobar_true_cond = Mock(status="True", type="foobar")

    node_mock1 = Mock(status=Mock(conditions=[ready_false_cond, foobar_true_cond]))
    node_mock2 = Mock(status=Mock(conditions=[ready_false_cond, foobar_true_cond]))

    kubernetes_service.get_nodes = MagicMock()
    kubernetes_service.get_nodes().items = [node_mock1, node_mock2]

    with pytest.raises(NodesNotReadyError):
      kubernetes_service.check_nodes_are_ready()

  def test_check_nodes_are_not_ready_no_nodes(self, kubernetes_service):
    kubernetes_service.get_nodes = MagicMock()
    kubernetes_service.get_nodes().items = []

    with pytest.raises(NodesNotReadyError):
      kubernetes_service.check_nodes_are_ready()

  def test_get_nodes(self, kubernetes_service):
    kubernetes_service._v1_core = Mock()
    kubernetes_service.get_nodes()

    kubernetes_service._v1_core.list_node.assert_called_with()

  def test_get_cluster_names(self, kubernetes_service):
    kubernetes_service._get_config_files = MagicMock(return_value=["config-test-cluster"])
    assert kubernetes_service.get_cluster_names() == ["test-cluster"]

    kubernetes_service._get_config_files = MagicMock(return_value=[])
    assert kubernetes_service.get_cluster_names() == []


# pylint: enable=protected-access
