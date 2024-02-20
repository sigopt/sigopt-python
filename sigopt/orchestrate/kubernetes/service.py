# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import base64
import errno
import json
import os
import shutil
import tempfile
import time
import urllib
from http import client as http_client

import backoff
import requests
import yaml
from kubernetes import client, config, utils, watch
from kubernetes.client.models.v1_container_image import V1ContainerImage
from OpenSSL import crypto

from sigopt.paths import ensure_dir, get_root_subdir

from ..exceptions import FileAlreadyExistsError, NodesNotReadyError, OrchestrateException
from ..provider.constants import Provider
from ..services.base import Service
from ..version import CLI_NAME
from .http_proxy import KubeProxyHTTPAdapter
import secrets


DEFAULT_NAMESPACE = "default"
ORCHESTRATE_NAMESPACE = "orchestrate"
KUBESYSTEM_NAMESPACE = "kube-system"
NVIDIA_DEVICE_PLUGIN_URL = "https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.9.0/nvidia-device-plugin.yml"


# NOTE: monkeypatch for containerd not naming all images (?)
# https://github.com/kubernetes-client/python/issues/895#issuecomment-515025300
# pylint: disable=all
def names(self, names):
  self._names = names


V1ContainerImage.names = V1ContainerImage.names.setter(names)
# pylint: enable=all


class NoNodesInClusterError(NodesNotReadyError):
  def __init__(self):
    super().__init__(
      "Looks like your cluster does not have any nodes. Please check that your"
      " cluster configuration file has defined either `cpu` or `gpu` nodes. For"
      " AWS clusters, check that you see nodes on the EC2 console."
    )


class NodeStatusNotReadyError(NodesNotReadyError):
  def __init__(self):
    super().__init__(
      f"None of your nodes are ready to go. Run `{CLI_NAME} kubectl get nodes` to see the status of your nodes."
    )


class KubernetesException(OrchestrateException):
  pass


class JobNotFoundException(KubernetesException):
  pass


class PodNotFoundException(KubernetesException):
  pass


class StartJobException(KubernetesException):
  pass


class CleanupFailedException(KubernetesException):
  pass


class KubernetesService(Service):
  def __init__(self, services):
    super().__init__(services)
    self._kube_config = None
    self._kube_dir = get_root_subdir("cluster")
    self._set_all_clients()

  def warmup(self):
    kube_configs = self._get_config_files()
    if kube_configs:
      self._kube_config = os.path.join(self._kube_dir, kube_configs[0])
    try:
      configuration = client.Configuration()
      config.load_kube_config(self._kube_config, client_configuration=configuration)
      if os.environ.get("HTTPS_PROXY"):
        configuration.proxy = os.environ["HTTPS_PROXY"]
      api_client = client.ApiClient(configuration)
      self._set_all_clients(api_client)
    except Exception as e:
      if "Invalid kube-config file. No configuration found." not in str(e):
        self.services.logging_service.warning(
          (
            "Experienced the following error while attempting to create"
            " kubernetes client from cluster"
            " configuration:\n%s\nDisconnecting and reconnecting may"
            " resolve the issue.\nPlease try"
            f" running:\n\t{CLI_NAME} cluster disconnect -a"
          ),
          str(e),
        )
      self._set_all_clients(None)

  @property
  def kube_config(self):
    return self._kube_config

  def get_jobs(self, job_name=None):
    if job_name:
      try:
        return self._v1_batch.read_namespaced_job(job_name, ORCHESTRATE_NAMESPACE)
      except client.rest.ApiException as e:
        if e.status == http_client.NOT_FOUND:
          raise JobNotFoundException(f"Job with name {job_name} not found") from e
        else:
          raise
    else:
      return self._v1_batch.list_namespaced_job(ORCHESTRATE_NAMESPACE, watch=False)

  def get_jobs_by_label_selector(self, label_selector):
    return self._v1_batch.list_namespaced_job(
      ORCHESTRATE_NAMESPACE,
      watch=False,
      label_selector=label_selector,
    )

  def delete_job(self, job_name, propogation_policy=None):
    try:
      self._v1_batch.delete_namespaced_job(
        job_name,
        ORCHESTRATE_NAMESPACE,
        body=client.V1DeleteOptions(propagation_policy=propogation_policy),
      )
    except client.rest.ApiException as e:
      if e.status == http_client.NOT_FOUND:
        raise JobNotFoundException(f"Job with name {job_name} not found") from e
      else:
        raise

  def start_job(self, job_spec_dict):
    try:
      return self._v1_batch.create_namespaced_job(ORCHESTRATE_NAMESPACE, job_spec_dict)
    except client.rest.ApiException as e:
      if e.status == http_client.BAD_REQUEST:
        k8s_error_message = json.loads(e.body).get("message")
        error_message = (
          "\n[ERROR]\t\tKubernetes reported a bad request this is most"
          " likely from an error in the experiment configuration"
          f" file.\n\t\tFormated Kubernetes Error:\n{k8s_error_message}\n"
        )
        raise StartJobException(error_message) from e
      else:
        raise

  # TODO: control how logs are displayed, should this be sent to stdout by subprocess or by the CLI?
  def logs(self, pod_name, follow=False):
    if follow:
      watcher = watch.Watch()
      return watcher.stream(
        self._v1_core.read_namespaced_pod_log,
        pod_name,
        ORCHESTRATE_NAMESPACE,
      )
    return self._v1_core.read_namespaced_pod_log(pod_name, ORCHESTRATE_NAMESPACE)

  def pod_names(self, job_name):
    data = self.get_pods(job_name=job_name)
    return [item.metadata.name for item in data.items]

  def get_pods_by_label_selector(self, label_selector):
    return self._v1_core.list_namespaced_pod(
      ORCHESTRATE_NAMESPACE,
      watch=False,
      label_selector=label_selector,
    )

  def get_pods(self, job_name=None):
    if job_name:
      return self.get_pods_by_label_selector(label_selector=f"job-name={job_name}")
    else:
      return self._v1_core.list_namespaced_pod(ORCHESTRATE_NAMESPACE, watch=False)

  def get_pod(self, pod_name):
    return self._v1_core.read_namespaced_pod(pod_name, ORCHESTRATE_NAMESPACE)

  def delete_pod(self, pod_name):
    return self._v1_core.delete_namespaced_pod(pod_name, ORCHESTRATE_NAMESPACE, body=client.V1DeleteOptions())

  def _watch_pod_events(self, iteratee, **kwargs):
    watcher = watch.Watch()
    event = None
    for event in watcher.stream(
      self._v1_core.list_namespaced_pod,
      ORCHESTRATE_NAMESPACE,
      **kwargs,
    ):
      if iteratee(event):
        break
    return event

  def wait_for_pod_to_exist(self, label_selector):
    return self._watch_pod_events(lambda e: True, label_selector=label_selector)["object"]

  def wait_for_pod_to_start(self, label_selector, event_handler=None):
    def iteratee(event):
      if event_handler:
        event_handler(event)
      return event["object"].status.phase in ("Running", "Succeeded", "Failed")

    return self._watch_pod_events(iteratee, label_selector=label_selector)["object"]

  def wait_until_nodes_are_ready(self, retries=20):
    for try_number in range(retries + 1):
      try:
        self.check_nodes_are_ready()
        return
      except NodesNotReadyError:
        if try_number >= retries:
          raise
        else:
          time.sleep(secrets.SystemRandom().uniform(20, 40))  # nosec

  def check_nodes_are_ready(self):
    nodes = self.get_nodes().items
    if not nodes:
      raise NoNodesInClusterError()

    any_node_ready = any(c.type == "Ready" and c.status == "True" for node in nodes for c in node.status.conditions)
    if not any_node_ready:
      raise NodeStatusNotReadyError()

  def ensure_config_map(self, config_map):
    try:
      self._v1_core.create_namespaced_config_map(KUBESYSTEM_NAMESPACE, config_map)
    except client.rest.ApiException as e:
      if e.status != http_client.CONFLICT:
        raise

  def write_config(self, cluster_name, data):
    ensure_dir(self._kube_dir)
    new_file_path = self._kube_config_path(cluster_name)
    if os.path.isfile(new_file_path):
      raise FileAlreadyExistsError(new_file_path)

    with open(new_file_path, "w") as f:
      yaml.dump(data, f)

    self.warmup()

  def test_config(self, retries=0, wait_time=5):
    if self._v1_core is None:
      raise OrchestrateException(
        "We ran into an issue connecting to your cluster."
        "\nDisconnecting and then reconnecting may resolve the issue."
        "\nDisconnect by running:"
        f"\n\t{CLI_NAME} cluster disconnect -a"
      )

    for try_number in range(retries + 1):
      try:
        return self._v1_core.list_namespaced_service(DEFAULT_NAMESPACE)
      except Exception:
        if try_number >= retries:
          raise
        else:
          time.sleep(wait_time)

  def ensure_config_deleted(self, cluster_name):
    try:
      self._delete_config(cluster_name)
    except OSError as e:
      if e.errno != errno.ENOENT:
        raise

  def get_cluster_names(self):
    return [self._cluster_name_from_config(c) for c in self._get_config_files()]

  def ensure_plugins(self, cluster_name, provider):
    with urllib.request.urlopen(NVIDIA_DEVICE_PLUGIN_URL) as nvidia_plugin_fp:
      self._ensure_plugin_fp(nvidia_plugin_fp, namespace=KUBESYSTEM_NAMESPACE)
    self.ensure_orchestrate_namespace()
    self._ensure_plugin("orchestrate-controller-roles.yml", namespace=ORCHESTRATE_NAMESPACE)
    # NOTE: disabled until remote image builds are working (consistently)
    self.ensure_docker_plugin(
      resources=dict(
        requests=dict(
          cpu="0.5",
          memory="2Gi",
        ),
      ),
      storage_capacity="512Gi",
    )
    if provider == Provider.AWS:
      self.create_autoscaler(cluster_name)

  def create_docker_tls_certs(self):
    ten_years = 10 * 365 * 24 * 60 * 60
    outputs = {}
    ca_key = crypto.PKey()
    ca_key.generate_key(crypto.TYPE_RSA, 4096)
    ca_cert = crypto.X509()
    ca_cert.get_subject().CN = "sigopt:docker ca"
    ca_cert.set_serial_number(secrets.SystemRandom().getrandbits(64))
    ca_cert.set_issuer(ca_cert.get_subject())
    ca_cert.set_pubkey(ca_key)
    ca_cert.gmtime_adj_notBefore(0)
    ca_cert.gmtime_adj_notAfter(ten_years)
    ca_cert.add_extensions(
      [
        crypto.X509Extension(b"basicConstraints", True, b"CA:TRUE, pathlen:0"),
        crypto.X509Extension(b"keyUsage", True, b"keyCertSign, cRLSign"),
        crypto.X509Extension(b"subjectKeyIdentifier", False, b"hash", subject=ca_cert),
      ]
    )
    ca_cert.sign(ca_key, "sha256")
    outputs["ca.pem"] = crypto.dump_certificate(crypto.FILETYPE_PEM, ca_cert).decode("ascii")
    server_key = crypto.PKey()
    server_key.generate_key(crypto.TYPE_RSA, 4096)
    outputs["key.pem"] = crypto.dump_privatekey(crypto.FILETYPE_PEM, server_key).decode("ascii")
    server_req = crypto.X509Req()
    server_req.get_subject().CN = "sigopt:docker server"
    server_req.set_pubkey(server_key)
    server_req.sign(ca_key, "sha256")
    server_cert = crypto.X509()
    server_cert.set_serial_number(secrets.SystemRandom().getrandbits(64))
    server_cert.gmtime_adj_notBefore(0)
    server_cert.gmtime_adj_notAfter(ten_years)
    server_cert.set_issuer(ca_cert.get_subject())
    server_cert.set_subject(server_req.get_subject())
    server_cert.set_pubkey(server_req.get_pubkey())
    server_cert.add_extensions(
      [
        crypto.X509Extension(
          b"subjectAltName",
          False,
          f"DNS:localhost, DNS:docker.{KUBESYSTEM_NAMESPACE}.svc.cluster.local, IP:127.0.0.1".encode(),
        ),
        crypto.X509Extension(b"extendedKeyUsage", False, b"serverAuth"),
      ]
    )
    server_cert.sign(ca_key, "sha256")
    outputs["cert.pem"] = crypto.dump_certificate(crypto.FILETYPE_PEM, server_cert).decode("ascii")
    return outputs

  def is_docker_installed(self):
    try:
      self._v1_apps.read_namespaced_stateful_set("docker", KUBESYSTEM_NAMESPACE)
      return True
    except client.rest.ApiException as e:
      if e.status != http_client.NOT_FOUND:
        raise
      return False

  def wait_for_docker_pod(self, sleep_time=5, iterations=6):
    for _ in range(iterations):
      try:
        docker_pod = self._v1_core.read_namespaced_pod("docker-0", KUBESYSTEM_NAMESPACE)
        if docker_pod.status.phase == "Running":
          return
      except client.rest.ApiException as e:
        if e.status != http_client.NOT_FOUND:
          raise
      time.sleep(sleep_time)
    raise TimeoutError(
      "\n".join(
        [
          "Timed out waiting for Docker to start.",
          "You can find more information by running the following:",
          "\tsigopt cluster kubectl -nkube-system describe pod/docker-0",
        ]
      )
    )

  def ensure_docker_plugin(self, resources, storage_capacity):
    docker_certs_secret_name = "docker-certs"
    try:
      self._v1_core.read_namespaced_secret(docker_certs_secret_name, KUBESYSTEM_NAMESPACE)
    except client.rest.ApiException as e:
      if e.status != http_client.NOT_FOUND:
        raise
      docker_certs = self.create_docker_tls_certs()
      self._v1_core.create_namespaced_secret(
        KUBESYSTEM_NAMESPACE,
        {
          "metadata": {
            "name": docker_certs_secret_name,
            "labels": {"app": "docker"},
          },
          "data": {key: base64.b64encode(value.encode()).decode("ascii") for key, value in docker_certs.items()},
          "type": "Opaque",
        },
      )

    with self.services.resource_service.open("plugins", "docker-statefulset.yml") as resource_fp:
      docker_stateful_set_template = yaml.safe_load(resource_fp)
    docker_stateful_set_template["spec"]["template"]["spec"]["containers"][0]["resources"] = resources
    docker_stateful_set_template["spec"]["volumeClaimTemplates"][0]["spec"]["resources"]["requests"][
      "storage"
    ] = storage_capacity
    self._apply_object(
      self._v1_apps.create_namespaced_stateful_set,
      self._v1_apps.patch_namespaced_stateful_set,
      docker_stateful_set_template,
      KUBESYSTEM_NAMESPACE,
    )
    with self.services.resource_service.open("plugins", "docker-service.yml") as resource_fp:
      docker_service_template = yaml.safe_load(resource_fp)
    self._apply_object(
      self._v1_core.create_namespaced_service,
      self._v1_core.patch_namespaced_service,
      docker_service_template,
      KUBESYSTEM_NAMESPACE,
    )

  def mount_http_proxy_adapter(self, session):
    session.mount(
      self._api_client.configuration.host,
      KubeProxyHTTPAdapter(k8s_api_client=self._api_client),
    )

  def get_docker_connection_url(self):
    return (
      f"{self._api_client.configuration.host}"
      f"/api/v1/namespaces/{KUBESYSTEM_NAMESPACE}/services/https:docker:https/proxy"
    )

  def cleanup_for_destroy(self):
    try:
      self._v1_apps.delete_namespaced_stateful_set("docker", KUBESYSTEM_NAMESPACE)
    except client.rest.ApiException as e:
      if e.status != http_client.NOT_FOUND:
        raise
    selector = "orchestrate/cleanup-before-destroy"
    for pvc in self._v1_core.list_persistent_volume_claim_for_all_namespaces(
      label_selector=selector,
    ).items:
      self._v1_core.delete_namespaced_persistent_volume_claim(pvc.metadata.name, pvc.metadata.namespace)
    remaining_pvs = backoff.on_predicate(backoff.expo, lambda pvs: len(pvs.items) > 0, max_time=120)(
      self._v1_core.list_persistent_volume
    )()
    if remaining_pvs.items:
      raise CleanupFailedException(
        "Some volumes could not be cleaned up, please remove them before destroying the cluster"
      )

  def ensure_orchestrate_namespace(self):
    try:
      self._v1_core.create_namespace(client.V1Namespace(metadata=client.V1ObjectMeta(name=ORCHESTRATE_NAMESPACE)))
    except client.rest.ApiException as e:
      if e.status != http_client.CONFLICT:
        raise

  def _ensure_plugin_fp(self, fp, namespace):
    with tempfile.NamedTemporaryFile("wb") as temp_fp:
      shutil.copyfileobj(fp, temp_fp)
      temp_fp.flush()
      try:
        utils.create_from_yaml(self._api_client, temp_fp.name)
      except utils.FailToCreateError as fce:
        if not all(exc.status == http_client.CONFLICT for exc in fce.api_exceptions):
          raise

  def _ensure_plugin(self, file_name, namespace):
    with self.services.resource_service.open("plugins", file_name) as file_content:
      self._ensure_plugin_fp(file_content, namespace)

  def _cluster_name_from_config(self, config_name):
    basename = os.path.basename(config_name)
    if basename.startswith("config-"):
      return basename[len("config-") :]
    else:
      return None

  def get_nodes(self):
    return self._v1_core.list_node()

  def _delete_config(self, cluster_name):
    self._kube_config = None
    self._set_all_clients()
    os.remove(self._kube_config_path(cluster_name))

  def _kube_config_path(self, cluster_name):
    filename = f"config-{cluster_name}"
    return os.path.join(self._kube_dir, filename)

  def _get_config_files(self):
    if os.path.exists(self._kube_dir):
      return [config for config in os.listdir(self._kube_dir) if config.startswith("config-")]
    return []

  def _set_all_clients(self, api_client=None):
    self._api_client = api_client
    if api_client:
      self._v1_apps = client.AppsV1Api(api_client)
      self._v1_batch = client.BatchV1Api(api_client)
      self._v1_core = client.CoreV1Api(api_client)
      self._v1_rbac = client.RbacAuthorizationV1Api(api_client)
    else:
      self._v1_apps = None
      self._v1_batch = None
      self._v1_core = None
      self._v1_rbac = None

  def _get_autoscaler_args(self, cluster_name):
    aws_provider = self.services.provider_broker.get_provider_service(Provider.AWS)
    aws_services = aws_provider.aws_services
    autoscaler_stack = aws_services.cloudformation_service.describe_eks_cluster_autoscaler_role_stack(cluster_name)
    autoscaler_role_arn = [
      out["OutputValue"] for out in autoscaler_stack.outputs if out["OutputKey"] == "ClusterAutoscalerRoleArn"
    ][0]

    kubernetes_version = aws_services.eks_service.describe_cluster(cluster_name)["cluster"]["version"]
    return (autoscaler_role_arn, kubernetes_version)

  def _get_autoscaler_image_version(self, kubernetes_version):
    k8s_version_to_autoscaler_release = {
      "1.20": "1.20.3",
      "1.21": "1.21.2",
    }
    return k8s_version_to_autoscaler_release.get(kubernetes_version, f"{kubernetes_version}.0")

  def _parameterize_autoscaler_dicts(self, cluster_name, autoscaler_role_arn, kubernetes_version):
    with self.services.resource_service.open("plugins", "autoscaler-plugin-template.yml") as fh:
      objs = list(yaml.safe_load_all(fh))
    (
      service_account_dict,
      cluster_role_dict,
      role_dict,
      cluster_role_binding_dict,
      role_binding_dict,
      deployment_dict,
    ) = objs

    service_account_dict["metadata"]["annotations"] = {
      "eks.amazonaws.com/role-arn": autoscaler_role_arn,
    }

    autoscaler_version = self._get_autoscaler_image_version(kubernetes_version)
    autoscaler_image = f"k8s.gcr.io/autoscaling/cluster-autoscaler:v{autoscaler_version}"
    deployment_dict["spec"]["template"]["spec"]["containers"][0]["image"] = autoscaler_image

    auto_discovery_tag = f"tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/{cluster_name}"
    auto_discovery_arg = f"--node-group-auto-discovery=asg:{auto_discovery_tag}"
    deployment_dict["spec"]["template"]["spec"]["containers"][0]["command"].append(auto_discovery_arg)
    return (
      service_account_dict,
      cluster_role_dict,
      role_dict,
      cluster_role_binding_dict,
      role_binding_dict,
      deployment_dict,
    )

  def _apply_object(self, create_func, patch_func, body, namespace=None):
    kwargs = {"body": body}
    if namespace is not None:
      kwargs["namespace"] = namespace
    try:
      create_func(**kwargs)
    except client.rest.ApiException as e:
      if e.status == http_client.CONFLICT:
        kwargs["name"] = body["metadata"]["name"]
        patch_func(**kwargs)
      else:
        raise

  def create_autoscaler(self, cluster_name):
    (autoscaler_role_arn, kubernetes_version) = self._get_autoscaler_args(cluster_name)
    autoscaler_dicts = self._parameterize_autoscaler_dicts(cluster_name, autoscaler_role_arn, kubernetes_version)
    (
      sa_dict,
      cluster_role_dict,
      role_dict,
      crb_dict,
      rb_dict,
      deployment_dict,
    ) = autoscaler_dicts
    self._apply_object(
      self._v1_core.create_namespaced_service_account,
      self._v1_core.patch_namespaced_service_account,
      sa_dict,
      KUBESYSTEM_NAMESPACE,
    )
    self._apply_object(
      self._v1_rbac.create_cluster_role,
      self._v1_rbac.patch_cluster_role,
      cluster_role_dict,
    )
    self._apply_object(
      self._v1_rbac.create_namespaced_role,
      self._v1_rbac.patch_namespaced_role,
      role_dict,
      KUBESYSTEM_NAMESPACE,
    )
    self._apply_object(
      self._v1_rbac.create_cluster_role_binding,
      self._v1_rbac.patch_cluster_role_binding,
      crb_dict,
    )
    self._apply_object(
      self._v1_rbac.create_namespaced_role_binding,
      self._v1_rbac.patch_namespaced_role_binding,
      rb_dict,
      KUBESYSTEM_NAMESPACE,
    )
    self._apply_object(
      self._v1_apps.create_namespaced_deployment,
      self._v1_apps.patch_namespaced_deployment,
      deployment_dict,
      KUBESYSTEM_NAMESPACE,
    )

  def _delete_autoscaler_object(self, delete_func, body, namespace=None):
    kwargs = {"name": body["metadata"]["name"]}
    if namespace is not None:
      kwargs["namespace"] = namespace
    try:
      delete_func(**kwargs)
    except client.rest.ApiException as e:
      if e.status != http_client.NOT_FOUND:
        raise

  def delete_autoscaler(self, cluster_name):
    (autoscaler_role_arn, kubernetes_version) = self._get_autoscaler_args(cluster_name)
    autoscaler_dicts = self._parameterize_autoscaler_dicts(cluster_name, autoscaler_role_arn, kubernetes_version)
    (
      sa_dict,
      cluster_role_dict,
      role_dict,
      crb_dict,
      rb_dict,
      deployment_dict,
    ) = autoscaler_dicts

    self._delete_autoscaler_object(
      self._v1_core.delete_namespaced_service_account,
      sa_dict,
      KUBESYSTEM_NAMESPACE,
    )
    self._delete_autoscaler_object(
      self._v1_rbac.delete_cluster_role,
      cluster_role_dict,
    )
    self._delete_autoscaler_object(
      self._v1_rbac.delete_namespaced_role,
      role_dict,
      KUBESYSTEM_NAMESPACE,
    )
    self._delete_autoscaler_object(
      self._v1_rbac.delete_cluster_role_binding,
      crb_dict,
    )
    self._delete_autoscaler_object(
      self._v1_rbac.delete_namespaced_role_binding,
      rb_dict,
      KUBESYSTEM_NAMESPACE,
    )
    self._delete_autoscaler_object(
      self._v1_apps.delete_namespaced_deployment,
      deployment_dict,
      KUBESYSTEM_NAMESPACE,
    )
