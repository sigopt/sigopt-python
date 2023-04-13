# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import os
import re
from collections import defaultdict

import click
import pint
import yaml
from botocore.exceptions import NoRegionError

from sigopt.paths import ensure_dir, get_bin_dir
from sigopt.utils import accept_sigopt_not_found

from .cluster.errors import AlreadyConnectedException, ClusterError, MultipleClustersConnectionError, NotConnectedError
from .docker.service import DockerException, DockerService
from .exceptions import CheckExecutableError, ModelPackingError, OrchestrateException
from .identifier import IDENTIFIER_TYPE_EXPERIMENT, IDENTIFIER_TYPE_RUN, parse_identifier
from .kubernetes.service import ORCHESTRATE_NAMESPACE, CleanupFailedException
from .paths import (
  check_iam_authenticator_executable,
  check_kubectl_executable,
  download_iam_authenticator_executable,
  download_kubectl_executable,
)
from .provider.constants import PROVIDER_TO_STRING, Provider
from .services.orchestrate_bag import OrchestrateServiceBag
from .status import print_status
from .stop import stop_experiment, stop_run


class _ExitException(click.ClickException):
  def __init__(self, msg, exit_code=1):
    super().__init__(msg)
    self.exit_code = exit_code


def docker_login(cluster, docker_service, repository_name):
  creds = cluster.get_registry_login_credentials(repository_name)
  if creds is not None:
    docker_service.login(creds)


class OrchestrateController:
  def __init__(self, services):
    self.services = services

  @classmethod
  def create(cls):
    try:
      services = OrchestrateServiceBag()
    except NoRegionError as e:
      raise _ExitException("No default region is selected, please run `aws configure`") from e
    return cls(services)

  def clean_images(self):
    self.services.cluster_service.assert_is_connected()
    docker_service = DockerService.create(self.services)
    docker_service.prune()

  def build_and_push_image(
    self,
    cluster,
    docker_service,
    dockerfile,
    run_options,
    quiet,
  ):
    image_name = run_options.get("image")
    repository_name, tag = DockerService.get_repository_and_tag(image_name)
    docker_login(cluster, docker_service, repository_name)

    build_image = run_options.get("build_image", True)

    if build_image:
      if not quiet:
        print("Containerizing and uploading your model, this may take a few minutes...")
      try:
        image_tag = self.services.model_packer_service.build_image(
          docker_service=docker_service,
          repository=repository_name,
          tag=tag,
          quiet=quiet,
          dockerfile=dockerfile,
        )
        image = docker_service.get_image(image_tag)
      except ModelPackingError as mpe:
        msg = str(mpe)
        match = re.search("manifest for (.*?) not found: manifest unknown: manifest unknown", msg)
        if match is not None:
          msg = f"Unable to find base image {match.groups()[0]} when building your docker container"
        raise _ExitException(msg) from mpe

    repository_name = cluster.generate_image_tag(repository_name)
    repository_image_tag = DockerService.format_image_name(repository_name, tag)
    if build_image:
      image.tag(repository=repository_name, tag=tag)
      if not quiet:
        print(f"Uploading the model environment to image registry: {repository_image_tag}")
      docker_service.push(repository_name, tag=tag, quiet=quiet)

    return repository_name, tag

  def runner(
    self,
    run_options,
    command,
    cluster,
    docker_service,
    dockerfile,
    project_id,
    quiet=False,
    optimize=True,
    optimization_options=None,
  ):
    if optimize:
      if not optimization_options:
        raise OrchestrateException("optimize jobs require an experiment yaml file")

    repository_name, tag = self.build_and_push_image(
      cluster=cluster,
      docker_service=docker_service,
      dockerfile=dockerfile,
      run_options=run_options,
      quiet=quiet,
    )

    resource_options = self.services.gpu_options_validator_service.get_resource_options(run_options)

    run_command = command

    job_type_str = "experiment" if optimize else "run"

    if not quiet:
      print("Starting your {}".format(job_type_str))

    if optimize:
      return self.services.job_runner_service.start_cluster_experiment(
        repository=repository_name,
        tag=tag,
        resource_options=resource_options,
        optimization_options=optimization_options,
        run_command=run_command,
        project_id=project_id,
      )
    return self.services.job_runner_service.start_cluster_run(
      repository=repository_name,
      tag=tag,
      resource_options=resource_options,
      run_command=run_command,
      project_id=project_id,
    )

  def run_on_cluster(self, command, run_options, silent, dockerfile, project_id):
    cluster = self.services.cluster_service.test()

    quiet = silent

    docker_service = DockerService.create(self.services)
    identifier = self.runner(
      cluster=cluster,
      docker_service=docker_service,
      quiet=quiet,
      optimize=False,
      command=command,
      run_options=run_options,
      dockerfile=dockerfile,
      project_id=project_id,
    )
    if quiet:
      print(identifier)
    else:
      print(f'Started "{identifier}"')

  def test_run_on_cluster(self, command, run_options, dockerfile, project_id):
    cluster = self.services.cluster_service.test()

    docker_service = DockerService.create(self.services)
    identifier = self.runner(
      cluster=cluster,
      docker_service=docker_service,
      quiet=False,
      optimize=False,
      run_options=run_options,
      dockerfile=dockerfile,
      command=command,
      project_id=project_id,
    )
    run_identifier = parse_identifier(identifier)
    label_selector = run_identifier["pod_label_selector"]
    print(f"View your run at https://app.sigopt.com/{identifier}")
    print("waiting for controller to start...")

    def check_pod_condition(event):
      if event["type"] == "DELETED":
        raise Exception("The pod was deleted")
      pod = event["object"]
      for condition in pod.status.conditions or []:
        if condition.type in ("Ready", "PodScheduled") and condition.status == "False":
          print(f"Pod '{pod.metadata.name}' in bad condition: {condition.reason}: {condition.message}")
        if condition.reason == "Unschedulable":
          print(
            "Hint: If you configured your nodes with sufficient resources"
            " then you probably just need to wait for the cluster to"
            " scale up"
          )
      for container_status in pod.status.container_statuses or []:
        waiting_state = container_status.state.waiting
        if waiting_state:
          print(
            f"Container '{container_status.name}' in pod"
            f" '{pod.metadata.name}' is waiting: {waiting_state.reason}:"
            f" {waiting_state.message}"
          )

    self.services.kubernetes_service.wait_for_pod_to_start(
      label_selector=run_identifier["controller_label_selector"],
      event_handler=check_pod_condition,
    )
    print("controller started, waiting for run to be created...")
    self.services.kubernetes_service.wait_for_pod_to_exist(label_selector=label_selector)
    print("run created, waiting for it to start...")
    pod = self.services.kubernetes_service.wait_for_pod_to_start(
      label_selector=label_selector,
      event_handler=check_pod_condition,
    )
    print("run started, following logs")
    try:
      print("*** START RUN LOGS ***")
      for log_line in self.services.kubernetes_service.logs(pod.metadata.name, follow=True):
        print(log_line)
      print("*** END RUN LOGS ***")
    except KeyboardInterrupt:
      print()
      print("Cleaning up")
      stop_run(run_identifier, self.services)

  def stop_by_identifier(self, identifier):
    identifier_type = identifier["type"]
    with accept_sigopt_not_found() as wrap:
      if identifier_type == IDENTIFIER_TYPE_RUN:
        stop_run(identifier, self.services)
      elif identifier_type == IDENTIFIER_TYPE_EXPERIMENT:
        stop_experiment(identifier, self.services)
      else:
        raise NotImplementedError(f"Cannot stop {identifier['raw']}")
    if wrap.exception:
      print(f"{identifier['raw']}: {str(wrap.exception)}")
    else:
      print(f"{identifier['raw']}: deleted")

  def optimize_on_cluster(self, command, run_options, optimization_options, silent, dockerfile, project_id):
    cluster = self.services.cluster_service.test()

    quiet = silent

    docker_service = DockerService.create(self.services)
    identifier = self.runner(
      cluster=cluster,
      docker_service=docker_service,
      quiet=quiet,
      optimize=True,
      command=command,
      run_options=run_options,
      optimization_options=optimization_options,
      dockerfile=dockerfile,
      project_id=project_id,
    )
    if quiet:
      print(identifier)
    else:
      print(f'Started "{identifier}"')

  def create_cluster(self, options):
    print("Creating your cluster, this process may take 20-30 minutes or longer...")

    # NOTE: checks again now that we know provider, in case aws iam authenticator is needed
    check_authenticator_binary(provider=options.get("provider"))
    try:
      cluster_name = self.services.cluster_service.create(options=options)
    except ClusterError as pde:
      raise _ExitException(str(pde)) from pde

    print(f"Successfully created kubernetes cluster: {cluster_name}")

  def update_cluster(self, options):
    print("Updating your cluster, this process may take 5-10 minutes or longer...")

    # NOTE: checks again now that we know provider, in case aws iam authenticator is needed
    check_authenticator_binary(provider=options.get("provider"))
    cluster_name = self.services.cluster_service.update(options=options)

    print(f"Successfully updated kubernetes cluster: {cluster_name}")

  def destroy_connected_cluster(self):
    cluster = self.services.cluster_service.get_connected_cluster()
    print(f"Destroying cluster {cluster.name}, this process may take 20-30 minutes or longer...")

    try:
      self.services.kubernetes_service.cleanup_for_destroy()
    except CleanupFailedException as cfe:
      raise _ExitException(str(cfe)) from cfe
    self.services.cluster_service.destroy(
      cluster_name=cluster.name,
      provider_string=cluster.provider_string,
    )
    print(f"Successfully destroyed kubernetes cluster: {cluster.name}")

  def connect_to_cluster(self, cluster_name, provider_string, registry, kubeconfig):
    check_authenticator_binary(provider=provider_string)

    print(f"Connecting to cluster {cluster_name}...")
    try:
      self.services.cluster_service.connect(
        cluster_name=cluster_name,
        provider_string=provider_string,
        kubeconfig=kubeconfig,
        registry=registry,
      )
      print(f"Successfully connected to kubernetes cluster: {cluster_name}")
    except AlreadyConnectedException as ace:
      raise _ExitException(
        f"Already connected to cluster: {ace.current_cluster_name}",
      ) from ace

  def disconnect_from_connected_cluster(self):
    cluster = self.services.cluster_service.get_connected_cluster()
    print(f"Disconnecting from cluster {cluster.name}...")

    try:
      self.services.cluster_service.disconnect(cluster.name, disconnect_all=False)
    except NotConnectedError:
      self.services.logging_service.warning("Not connected to any clusters")
    except MultipleClustersConnectionError as mcce:
      cluster_names = ", ".join(mcce.connected_clusters)
      self.services.logging_service.warning(
        f"Connected to multiple clusters: {cluster_names}. Rerun with `disconnect --all`."
      )
    except ClusterError as ce:
      raise _ExitException(str(ce)) from ce

  def test_cluster_connection(self):
    print("Testing if you are connected to a cluster, this may take a moment...")
    try:
      cluster = self.services.cluster_service.test()
    except NotConnectedError as nce:
      raise _ExitException(
        "You are not currently connected to a cluster.",
      ) from nce

    registry_str = cluster.registry if cluster.registry is not None else "default"
    print(
      "\nYou are connected to a cluster! Here is the info:"
      f"\n\tcluster name: {cluster.name}"
      f"\n\tprovider: {cluster.provider_string}"
      f"\n\tregistry: {registry_str}"
    )

    try:
      docker_service = DockerService.create(self.services)
      docker_service.check_connection()
    except DockerException as e:
      raise _ExitException(str(e)) from e

  def cluster_status(self):
    try:
      cluster = self.services.cluster_service.test()
    except NotConnectedError as nce:
      raise _ExitException(
        "You are not currently connected to a cluster",
      ) from nce

    print(f"You are currently connected to the cluster: {cluster.name}")
    all_pods = self.services.kubernetes_service.get_pods()
    nodes = self.services.kubernetes_service.get_nodes()
    individual_pods = []
    experiment_pods = defaultdict(list)

    def group_by_phase(pods):
      pods_by_phase = defaultdict(list)
      for pod in pods:
        pods_by_phase[pod.status.phase].append(pod)
      return pods_by_phase

    collapse_phases = ["Succeeded"]

    def print_pods(all_pods, indent):
      by_phase = group_by_phase(all_pods)
      tabs = "\t" * indent
      for phase, pods in by_phase.items():
        print(f"{tabs}{phase}: {len(pods)} runs")
        if phase not in collapse_phases:
          for p in pods:
            print(f"{tabs}\trun/{p.metadata.labels['run']}\t{p.metadata.name}")

    for pod in all_pods.items:
      if pod.metadata.labels["type"] == "run":
        try:
          experiment_pods[pod.metadata.labels["experiment"]].append(pod)
        except KeyError:
          individual_pods.append(pod)
    if individual_pods:
      print(f"One-off: {len(individual_pods)} runs")
      print_pods(individual_pods, 1)
    if experiment_pods:
      print(f"Experiments: {len(experiment_pods)} total")
      for eid, exp_pods in sorted(experiment_pods.items(), key=lambda x: x[0]):
        print(f"\texperiment/{eid}: {len(exp_pods)} runs")
        print_pods(exp_pods, 2)

    print(f"Nodes: {len(nodes.items)} total")
    running_pods_by_node = defaultdict(list)
    for pod in all_pods.items:
      if pod.status.phase == "Running":
        running_pods_by_node[pod.spec.node_name].append(pod)
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "nvidia.com/gpu"
    RESOURCE_META = ((CPU, "CPU"), (MEMORY, "B"), (GPU, "GPU"))
    unit_registry = pint.UnitRegistry()
    # NOTE: creates a new unit "CPU". "mCPU = milli CPU = 0.001 * CPU"
    unit_registry.define("CPU = [cpu]")
    unit_registry.define("GPU = [gpu]")
    for node in nodes.items:
      print(f"\t{node.metadata.name}:")
      node_resources = [
        (c.resources.requests, c.resources.limits)
        for p in running_pods_by_node[node.metadata.name]
        for c in p.spec.containers
      ]
      # NOTE: create an inital value for each resource type for requests and limits
      all_totals = tuple(
        {resource_type: 0 * unit_registry(ext) for resource_type, ext in RESOURCE_META} for _ in range(2)
      )
      for resources in node_resources:
        for resource_allocation, totals in zip(resources, all_totals):
          if not resource_allocation:
            continue
          for resource_type, ext in RESOURCE_META:
            # NOTE: this parses the resource quantity with a magnitude and unit.
            # ex. "12Mi" + "B" == "12*2^20 bytes", "100m" + "CPU" == "0.1 CPU"
            totals[resource_type] += unit_registry.Quantity(resource_allocation.get(resource_type, "0") + ext)
      requests_totals, limits_totals = all_totals
      for resource_type, ext in RESOURCE_META:
        allocatable = unit_registry.Quantity(node.status.allocatable.get(resource_type, "0") + ext)
        if not allocatable:
          continue
        print(f"\t\t{resource_type}:")
        total_request = requests_totals[resource_type]
        percent_request = (100 * total_request / allocatable).to_reduced_units()
        total_limit = limits_totals[resource_type]
        percent_limit = (100 * total_limit / allocatable).to_reduced_units()
        allocatable, total_request, total_limit = (
          value.to_compact() for value in (allocatable, total_request, total_limit)
        )
        print(f"\t\t\tAllocatable: {allocatable:~.2f}")
        print(f"\t\t\tRequests: {total_request:~.2f}, {percent_request:~.2f} %")
        print(f"\t\t\tLimits: {total_limit:~.2f}, {percent_limit:~.2f} %")

  def print_status(self, identifier):
    print(f"{identifier['raw']}:")
    with accept_sigopt_not_found() as wrap:
      for line in print_status(identifier, self.services):
        print(f"\t{line}")
    if wrap.exception:
      print(f"\t{str(wrap.exception)}")

  def install_cluster_plugins(self):
    cluster = self.services.cluster_service.get_connected_cluster()
    print("Installing required kubernetes resources...")
    self.services.kubernetes_service.ensure_plugins(cluster.name, cluster.provider)
    print("Uploading required images to your registry...")
    print("Finished installing plugins")

  def exec_kubectl(self, arguments):
    self.services.cluster_service.assert_is_connected()
    check_binary(kubectl_check)
    cmd = self.services.kubectl_service.get_kubectl_command()
    args = [cmd, "--namespace", ORCHESTRATE_NAMESPACE, *arguments]
    os.execvpe(
      cmd,
      args,
      env=self.services.kubectl_service.get_kubectl_env(),
    )


kubectl_check = (check_kubectl_executable, download_kubectl_executable, "kubernetes")
aws_iam_authenticator_check = (
  check_iam_authenticator_executable,
  download_iam_authenticator_executable,
  "aws iam-authentication",
)


def check_authenticator_binary(provider):
  if provider == PROVIDER_TO_STRING[Provider.AWS]:
    check_binary(aws_iam_authenticator_check)


def check_binary(options):
  ensure_dir(get_bin_dir())
  check, download, name = options
  try:
    check()
  except CheckExecutableError:
    print(f"Downloading {name} executable, this could take some time...")
    download()
    check(full_check=True)


def load_user_options(filename):
  with open(filename) as f:
    options = yaml.safe_load(f) or {}
  return options
