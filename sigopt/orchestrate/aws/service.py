# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import datetime
import re
import sys
import time
import types

import yaml
from botocore.exceptions import ClientError

from ..cluster.object import AWSCluster
from ..eks.service import DEFAULT_KUBERNETES_VERSION, SUPPORTED_KUBERNETES_VERSIONS
from ..exceptions import AwsClusterSharePermissionError, AwsPermissionsError, ClusterDestroyError, OrchestrateException
from ..node_groups import ALL_NODE_GROUP_TYPES, NODE_GROUP_TYPE_CPU, NODE_GROUP_TYPE_GPU, NODE_GROUP_TYPE_SYSTEM
from ..paths import get_executable_path
from ..provider.constants import Provider
from ..provider.interface import ProviderInterface


def is_cuda_gpu_instance_type(instance_type):
  prefix, _ = instance_type.split('.', 1)
  return prefix in ('p4d', 'p3', 'p3dn', 'p2', 'g4dn', 'g3')


def catch_aws_permissions_errors(func):
  def wrapper(*args, **kwargs):
    try:
      return func(*args, **kwargs)
    except ClientError as e:
      code = e.response['Error']['Code']
      http_status_code = e.response['ResponseMetadata']['HTTPStatusCode']
      if http_status_code == 403 or code in ('AccessDeniedException', 'UnauthorizedOperation'):
        raise AwsPermissionsError(e) from e
      raise
  return wrapper

def make_role_config_map(node_instance_role_arn, cluster_access_role_arn, cluster_access_role_name):
  map_roles = [
    {
      "rolearn": node_instance_role_arn,
      "username": "system:node:{{EC2PrivateDNSName}}",
      "groups": ["system:bootstrappers", "system:nodes"],
    },
    {
      "rolearn": cluster_access_role_arn,
      "username": cluster_access_role_name,
      "groups": ["system:masters"],
    },
  ]
  return {
    "apiVersion": "v1",
    "kind": "ConfigMap",
    "metadata": {
      "name": "aws-auth",
      "namespace": "kube-system",
    },
    "data": {
      "mapRoles": yaml.dump(map_roles),
    },
  }

class AwsService(ProviderInterface):
  def __init__(self, services, aws_services):
    super().__init__(services)
    self.aws_services = aws_services

  def __getattribute__(self, name):
    attr = super().__getattribute__(name)
    if isinstance(attr, types.MethodType):
      attr = catch_aws_permissions_errors(attr)
    return attr

  def describe_kubernetes_cluster(self, cluster_name):
    try:
      return self.aws_services.eks_service.describe_cluster(cluster_name=cluster_name)['cluster']
    except self.aws_services.eks_service.client.exceptions.ResourceNotFoundException as e:
      raise OrchestrateException(
        f"We cannot find an EKS cluster named '{cluster_name}' using your current AWS credentials."
        " Did someone delete this cluster?"
      ) from e

  def validate_cluster_options(self, cluster_name, node_groups_config, kubernetes_version):
    if kubernetes_version == "latest":
      kubernetes_version = DEFAULT_KUBERNETES_VERSION
    if kubernetes_version:
      assert kubernetes_version in SUPPORTED_KUBERNETES_VERSIONS, (
        'Unsupported kubernetes version for EKS:'
        f' {kubernetes_version}. Must be one of: {SUPPORTED_KUBERNETES_VERSIONS}'
      )

    cpu_nodes_config = node_groups_config.get(NODE_GROUP_TYPE_CPU)
    gpu_nodes_config = node_groups_config.get(NODE_GROUP_TYPE_GPU)

    assert cpu_nodes_config or gpu_nodes_config, "Looks like your cluster config file is not" \
      " asking us to spin up any CPU or GPU machines."
    name_regex = '^[a-zA-Z][-a-zA-Z0-9]*$'
    assert cluster_name and re.match(name_regex, cluster_name), \
      'Cluster names for AWS must match the regex: /' + name_regex + '/'

    if gpu_nodes_config:
      gpu_instance_type = gpu_nodes_config['instance_type']
      assert is_cuda_gpu_instance_type(gpu_instance_type), (
        f"GPUs are not supported on the instance type ({gpu_instance_type})"
      )

  def _handle_stack_event(self, _, event):
    resource_status = event["ResourceStatus"]
    logical_id = event["LogicalResourceId"]
    print(f"{resource_status} {event['ResourceType']} {logical_id} {event['PhysicalResourceId']}")
    if resource_status.endswith("_FAILED"):
      print(f"Error {resource_status}: {logical_id}: {event['ResourceStatusReason']}", file=sys.stderr)

  def get_node_groups(self, options):
    return {
      node_group_type: options.get(node_group_type) or {}
      for node_group_type in ALL_NODE_GROUP_TYPES
    }

  def _create_or_update_kubernetes_cluster(self, options, update):
    start_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    cluster_name = options['cluster_name']
    kubernetes_version = options.get('kubernetes_version') or DEFAULT_KUBERNETES_VERSION
    node_groups = self.get_node_groups(options)
    self.validate_cluster_options(cluster_name, node_groups, kubernetes_version)

    aws_options = options.get('aws') or {}
    additional_policies = aws_options.get('additional_policies') or []

    common_kwargs = dict(
      cluster_name=cluster_name,
      system_node_config=node_groups[NODE_GROUP_TYPE_SYSTEM],
      cpu_node_config=node_groups[NODE_GROUP_TYPE_CPU],
      gpu_node_config=node_groups[NODE_GROUP_TYPE_GPU],
      key_name=self.aws_services.ec2_service.ensure_key_pair_for_cluster(cluster_name).name,
      kubernetes_version=kubernetes_version,
    )

    if update:
      eks_cluster_stack = self.aws_services.cloudformation_service.update_eks_cluster_stack(
        event_handler=self._handle_stack_event,
        **common_kwargs,
      )
    else:
      try:
        eks_cluster_stack = self.aws_services.cloudformation_service.ensure_eks_cluster_stack(
            **common_kwargs,
        )
        self.aws_services.cloudformation_service.wait_for_stack_create_complete(
          eks_cluster_stack.name,
          event_handler=self._handle_stack_event,
          after=start_time,
        )
      except Exception as e:
        print("*" * 50)
        print("ERROR: encountered an error creating EKS cluster; tearing down resources")
        print("*" * 50)
        # TODO(dan): can we catch something more fine-grained here?
        # NOTE(dan): since we're just raising here anyway, we don't need to try-except?
        self.aws_services.cloudformation_service.ensure_eks_cluster_stack_deleted(
          cluster_name,
          self._handle_stack_event,
        )
        raise e
    eks_cluster_stack.reload()
    eks_cluster_stack_outputs = {
      o['OutputKey']: o['OutputValue']
      for o in eks_cluster_stack.outputs
    }
    node_instance_role_arn = eks_cluster_stack_outputs["NodeInstanceRoleArn"]

    for policy_arn in additional_policies:
      self.aws_services.iam_service.attach_policy(node_instance_role_arn, policy_arn)

    # NOTE(taylor): no reason to update the autoscaler role stack yet, just create it if it doesn't already exist
    eks_cluster = self.aws_services.eks_service.describe_cluster(cluster_name)
    self.aws_services.iam_service.ensure_eks_oidc_provider(eks_cluster)
    eks_cluster_autoscaler_role_stack = (
      self.aws_services.cloudformation_service.ensure_eks_cluster_autoscaler_role_stack(
        cluster_name=cluster_name,
        cluster_oidc_provider_url=eks_cluster["cluster"]["identity"]["oidc"]["issuer"],
      )
    )
    self.aws_services.cloudformation_service.wait_for_stack_create_complete(
      eks_cluster_autoscaler_role_stack.name,
      event_handler=self._handle_stack_event,
      after=start_time,
    )

    if not update:
      self._connect_kubernetes_cluster(cluster_name=cluster_name, ignore_role=True)
      self.test_kubernetes_cluster(cluster_name=cluster_name, ignore_role=True)

      # NOTE(taylor): no reason to update the aws-auth config map yet
      role_arn = eks_cluster_stack_outputs["ClusterAccessRoleArn"]
      role_name = eks_cluster_stack_outputs["ClusterAccessRoleName"]
      role_config_map = make_role_config_map(
        node_instance_role_arn=node_instance_role_arn,
        cluster_access_role_arn=role_arn,
        cluster_access_role_name=role_name,
      )
      self.services.kubernetes_service.ensure_config_map(role_config_map)

    self._disconnect_kubernetes_cluster(cluster_name=cluster_name)

    print('Testing your kubernetes configuration, you may see an error below but we should be able to resolve it...')
    self._connect_kubernetes_cluster(cluster_name=cluster_name)
    print('Successfully tested your kubernetes configuration, if you saw any errors above you may ignore them...')
    self._test_cluster_access_role(cluster_name=cluster_name, retries=3)
    # Note(Nakul): We disconnect and reconnect to solve an intermittent issue where the kubernetes python client
    # ends up with an empty api key. This is a temporary fix while we resolve the bug. This solves the issue by
    # reloading the key from the config file a second time which I found out works simply by some trial and error.
    self._disconnect_kubernetes_cluster(cluster_name=cluster_name)
    self._connect_kubernetes_cluster(cluster_name=cluster_name)

    self.test_kubernetes_cluster(cluster_name=cluster_name)

    self.services.kubernetes_service.ensure_plugins(cluster_name, Provider.AWS)

    print(self._node_access_instructions(cluster_name))

    return self.create_cluster_object(
      services=self.services,
      name=cluster_name,
      registry=None,
    )

  def create_kubernetes_cluster(self, options):
    return self._create_or_update_kubernetes_cluster(options, update=False)

  def update_kubernetes_cluster(self, options):
    return self._create_or_update_kubernetes_cluster(options, update=True)

  def _test_cluster_access_role(self, cluster_name, retries=0, wait_time=5):
    cluster_access_role_arn = self.aws_services.iam_service.get_cluster_access_role_arn(cluster_name)
    for try_number in range(retries + 1):
      try:
        self.aws_services.sts_service.assume_role(role_arn=cluster_access_role_arn)
      except ClientError as ce:
        if try_number >= retries:
          raise AwsClusterSharePermissionError(
            f"You do not have permission to use the role '{cluster_access_role_arn}' for accessing this cluster.\n"
            "Please read the SigOpt documentation for sharing clusters: "
            "https://app.sigopt.com/docs/orchestrate/deep_dive#cluster_sharing"
          ) from ce
        time.sleep(wait_time)

  def _connect_kubernetes_cluster(self, cluster_name, ignore_role=False):
    kubeconfig = self.create_kubeconfig(cluster_name, ignore_role)
    self.services.kubernetes_service.write_config(
      cluster_name=cluster_name,
      data=kubeconfig,
    )

  def test_kubernetes_cluster(self, cluster_name, ignore_role=False):
    if not ignore_role:
      self._test_cluster_access_role(cluster_name=cluster_name, retries=3)
    self.services.kubernetes_service.test_config()

  def _disconnect_kubernetes_cluster(self, cluster_name):
    self.services.kubernetes_service.ensure_config_deleted(cluster_name=cluster_name)

  def create_kubeconfig(self, cluster_name, ignore_role=False):
    cluster = self.describe_kubernetes_cluster(cluster_name)

    if ignore_role:
      cluster_access_role_arn = None
    else:
      cluster_access_role_arn = self.aws_services.iam_service.get_cluster_access_role_arn(cluster_name)

    # TODO(alexandra): optional role_arn is NOT the role ARN used to create the cluster
    # See Step 2 of https://docs.aws.amazon.com/eks/latest/userguide/getting-started.html

    kubeconfig = self.services.resource_service.load_yaml("eks", "kubeconfig.yml")
    kubeconfig["clusters"][0]["cluster"] = {
      "server": cluster["endpoint"],
      "certificate-authority-data": cluster["certificateAuthority"]["data"],
    }
    command_args = ["token", "-i", cluster_name]
    if cluster_access_role_arn:
      command_args.extend(["-r", cluster_access_role_arn])
    user = {
      "exec": {
        "apiVersion": "client.authentication.k8s.io/v1beta1",
        "command": get_executable_path("aws-iam-authenticator"),
        "args": command_args,
      },
    }
    kubeconfig["users"][0]["user"] = user
    return kubeconfig

  def destroy_kubernetes_cluster(self, cluster_name):
    self.services.kubernetes_service.ensure_config_deleted(cluster_name)
    self.aws_services.ec2_service.ensure_key_pair_for_cluster_deleted(cluster_name)

    try:
      instance_role_arn = self.aws_services.cloudformation_service.get_node_instance_role_arn(cluster_name)
      if instance_role_arn:
        instance_role = self.aws_services.iam_service.get_role_from_arn(instance_role_arn)
        for policy in instance_role.attached_policies.all():
          instance_role.detach_policy(PolicyArn=policy.arn)
    except ClientError:
      pass

    try:
      eks_cluster = self.aws_services.eks_service.describe_cluster(cluster_name)
      self.aws_services.iam_service.ensure_eks_oidc_provider_deleted(eks_cluster)
    except self.aws_services.eks_service.client.exceptions.ResourceNotFoundException:
      pass

    try:
      self.aws_services.cloudformation_service.ensure_eks_cluster_autoscaler_role_stack_deleted(
        cluster_name,
        event_handler=self._handle_stack_event,
      )
      self.aws_services.cloudformation_service.ensure_eks_cluster_stack_deleted(
        cluster_name,
        event_handler=self._handle_stack_event,
      )
    except Exception as e:
      raise ClusterDestroyError from e

  def _node_access_instructions(self, cluster_name):
    filename = self.aws_services.ec2_service.key_pair_location(cluster_name)
    return (
      '*Optional:'
      '\n\tTo ssh into any ec2 node in your cluster, use the username `ec2-user` with the key pair located at:'
      f'\n\t\t{filename}'
      '\n\tExample:'
      f'\n\t\tssh -i {filename} ec2-user@<node_dns_name>'
      '\n\tYou may be required to change security groups on your ec2 instances'
      '\n\tInstructions: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AccessingInstancesLinux.html'
    )

  def create_cluster_object(self, services, name, registry):
    return AWSCluster(
      services=services,
      name=name,
      registry=registry,
    )
