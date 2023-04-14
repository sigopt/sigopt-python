# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import collections
import datetime
import socket
import struct
import time

import backoff
import boto3
import botocore

from ..exceptions import OrchestrateException
from ..services.aws_base import AwsService


DEFAULT_SYSTEM_NODE_GROUP_MIN_NODES = 1
DEFAULT_SYSTEM_NODE_GROUP_MAX_NODES = 2
DEFAULT_SYSTEM_NODE_GROUP_INSTANCE_TYPE = "t3.large"

_call_boto_with_backoff = backoff.on_exception(
  backoff.expo,
  botocore.exceptions.ClientError,
  giveup=lambda ce: ce.response["Error"]["Code"] != "Throttling",
)


class FailedEksStackCreationError(OrchestrateException):
  def __init__(self, stack_name, stack_events):
    super().__init__(f"Failed to create EKS stack: {stack_name}")
    self.stack_name = stack_name
    self.stack_events = stack_events


class StackDeletedException(OrchestrateException):
  pass


# NOTE: Anatomy of VPC addresses
# AWS doesn't support masks smaller than /16
# ipv4: 192     .168     .0       .0
# bits: 11000000.10101000.00000000.000000000
# desc: aaaaaaaa.aaaaaaaa.bbcdddee.eeeeeeeee
#   a: mask
#   b: future use
#   c: public/private
#   d: availability zone number
#   e: addresses available within subnet (2^10 - 1 = 1023 addresses in each subnet)

IP_AZ_ALLOCATED_BITS = 3
IP_PRIVATE_PUBLIC_BITS = 1
IP_REMAINING_BITS = 10
IP_MASK_BITS = 16
VPC_HOST_IP = "192.168.0.0"
VPC_BLOCK = f"{VPC_HOST_IP}/{IP_MASK_BITS}"


class AwsCloudFormationService(AwsService):
  def __init__(self, services, aws_services, **kwargs):
    super().__init__(services, aws_services)
    self._client = boto3.client("cloudformation", **kwargs)
    self._cloudformation = boto3.resource("cloudformation", **kwargs)
    self.ec2 = boto3.client("ec2", **kwargs)

  @property
  def client(self):
    return self._client

  @property
  def cloudformation(self):
    return self._cloudformation

  def eks_cluster_autoscaler_role_stack_name(self, cluster_name):
    return f"{cluster_name}-eks-cluster-autoscaler-role"

  def create_eks_cluster_autoscaler_role_stack(self, cluster_name, cluster_oidc_provider_url):
    sg_template = self.services.resource_service.read(
      "cloudformation",
      "cluster-autoscaler-role.yaml",
    ).decode("utf-8")

    return self.cloudformation.create_stack(
      StackName=self.eks_cluster_autoscaler_role_stack_name(cluster_name),
      TemplateBody=sg_template,
      Parameters=[
        dict(
          ParameterKey=k,
          ParameterValue=v,
        )
        for (k, v) in [
          ("ClusterName", cluster_name),
          ("ClusterOIDCProviderURL", cluster_oidc_provider_url),
        ]
      ],
      Capabilities=[
        "CAPABILITY_IAM",
      ],
    )

  def delete_eks_cluster_autoscaler_role_stack(self, cluster_name):
    self.describe_eks_cluster_autoscaler_role_stack(cluster_name).delete()

  def describe_eks_cluster_autoscaler_role_stack(self, cluster_name):
    return self.cloudformation.Stack(self.eks_cluster_autoscaler_role_stack_name(cluster_name))

  def ensure_eks_cluster_autoscaler_role_stack(self, cluster_name, *args, **kwargs):
    try:
      self.create_eks_cluster_autoscaler_role_stack(cluster_name, *args, **kwargs)
    except self.client.exceptions.AlreadyExistsException:
      pass

    return self.describe_eks_cluster_autoscaler_role_stack(cluster_name)

  def ensure_eks_cluster_autoscaler_role_stack_deleted(self, cluster_name, event_handler=None):
    self._ensure_stack_deleted(
      self.eks_cluster_autoscaler_role_stack_name(cluster_name),
      event_handler=event_handler,
    )

  def eks_cluster_stack_name(self, cluster_name):
    return f"{cluster_name}-stack"

  def upload_stack_template(self, template_name):
    return self.aws_services.s3_service.upload_resource_by_hash(
      path_prefix="stack_templates",
      package="cloudformation",
      resource_name=template_name,
    )

  def _page_boto(self, func, params, results_key):
    next_token = None
    while True:
      params_ = params.copy()
      if next_token:
        params_["NextToken"] = next_token
      result = _call_boto_with_backoff(func)(**params)
      yield from result[results_key]
      next_token = result.get("NextToken")
      if not next_token:
        return

  def get_compatible_availability_zones_for_instance_types(self, instance_types, az_count, prev_azs=None):
    supported_azs = set.intersection(
      *(
        set(
          r["Location"]
          for r in self._page_boto(
            self.ec2.describe_instance_type_offerings,
            {
              "LocationType": "availability-zone",
              "Filters": [
                {"Name": "instance-type", "Values": [it]},
              ],
            },
            "InstanceTypeOfferings",
          )
        )
        for it in instance_types
      )
    )
    assert len(supported_azs) >= az_count, (
      "Not able to find enough supported availability zones for all of the"
      f" provided instance types: instance types: {instance_types}, required zone"
      f" count: {az_count}, supported zones: {supported_azs}"
    )
    if prev_azs:
      if not all(az in supported_azs for az in prev_azs):
        raise ValueError("The supported availability zones are not compatible with the previous availability zones")
      return prev_azs
    return sorted(supported_azs)[:az_count]

  def get_cidr_block(self, public, az):
    # NOTE: ">" = big endian (most significant bit first), "I" = unsigned integer
    network_i = struct.unpack(">I", socket.inet_aton(VPC_HOST_IP))[0]
    if not public:
      network_i |= 1 << (IP_REMAINING_BITS + IP_AZ_ALLOCATED_BITS)
    zone_number = ord(az[-1]) - ord("a")
    assert 0 <= zone_number <= (1 << IP_AZ_ALLOCATED_BITS)
    network_i |= zone_number << IP_REMAINING_BITS
    network = socket.inet_ntoa(struct.pack(">I", network_i))
    return f"{network}/{32 - IP_REMAINING_BITS}"

  def get_kwargs_for_cluster_stack(
    self,
    cluster_name,
    kubernetes_version,
    key_name,
    system_node_config,
    cpu_node_config,
    gpu_node_config,
    stack=None,
  ):
    system_max_nodes = system_node_config.get("max_nodes", DEFAULT_SYSTEM_NODE_GROUP_MAX_NODES)
    system_instance_type = system_node_config.get("instance_type", DEFAULT_SYSTEM_NODE_GROUP_INSTANCE_TYPE)
    cpu_min_nodes = cpu_node_config.get("min_nodes", 0)
    cpu_max_nodes = cpu_node_config.get("max_nodes", 0)
    cpu_instance_type = cpu_node_config.get("instance_type", "")
    cpu_node_volume_size = cpu_node_config.get("node_volume_size")
    gpu_min_nodes = gpu_node_config.get("min_nodes", 0)
    gpu_max_nodes = gpu_node_config.get("max_nodes", 0)
    gpu_instance_type = gpu_node_config.get("instance_type", "")
    gpu_node_volume_size = gpu_node_config.get("node_volume_size")
    parameters = dict(
      UserArn=self.aws_services.iam_service.get_user_arn(),
      ClusterName=cluster_name,
      KubernetesVersion=kubernetes_version,
      SystemNodeAutoScalingGroupMaxSize=str(system_max_nodes),
      SystemNodeInstanceType=system_instance_type,
      CPUNodeAutoScalingGroupMinSize=str(cpu_min_nodes),
      CPUNodeAutoScalingGroupDesiredCapacity=str(cpu_min_nodes),
      CPUNodeAutoScalingGroupMaxSize=str(cpu_max_nodes),
      CPUNodeInstanceType=cpu_instance_type,
      GPUNodeAutoScalingGroupMinSize=str(gpu_min_nodes),
      GPUNodeAutoScalingGroupDesiredCapacity=str(gpu_min_nodes),
      GPUNodeAutoScalingGroupMaxSize=str(gpu_max_nodes),
      GPUNodeInstanceType=gpu_instance_type,
      SSHKeyName=key_name,  # TODO: generate for user
    )
    for volume_size, param in [
      (cpu_node_volume_size, "CPUNodeVolumeSize"),
      (gpu_node_volume_size, "GPUNodeVolumeSize"),
    ]:
      if volume_size:
        parameters[param] = str(volume_size)

    instance_types = [
      instance_type
      for max_nodes, instance_type in [
        (system_max_nodes, system_instance_type),
        (cpu_max_nodes, cpu_instance_type),
        (gpu_max_nodes, gpu_instance_type),
      ]
      if max_nodes > 0
    ]
    prev_azs = None
    if stack:
      prev_parameters = {p["ParameterKey"]: p["ParameterValue"] for p in stack.parameters}
      # NOTE: Changing availability zones is extremely complicated, maybe even impossible without creating a new
      # cluster. This is because the EKS cluster is created with specific subnets that can't be modified.
      prev_azs = (prev_parameters["AZ01"], prev_parameters["AZ02"])

    try:
      az1, az2 = self.get_compatible_availability_zones_for_instance_types(instance_types, 2, prev_azs)
    except ValueError as ve:
      raise Exception(
        "The requested update cannot be done in-place. Please destroy your"
        " existing cluster and make a new one if you would like to proceed."
      ) from ve

    for param, public, az in [
      ("PublicSubnet01Block", True, az1),
      ("PublicSubnet02Block", True, az2),
      ("PrivateSubnet01Block", False, az1),
      ("PrivateSubnet02Block", False, az2),
    ]:
      parameters[param] = self.get_cidr_block(public, az)

    parameters["AZ01"] = az1
    parameters["AZ02"] = az2

    parameters["VPCBlock"] = VPC_BLOCK

    eks_cluster_stack_template_url = self.upload_stack_template("eks-cluster.yaml")
    for parameter_name, template_name in [
      ("NodeGroupStackTemplateURL", "eks-nodegroup.yaml"),
      ("NodeSecurityStackTemplateURL", "eks-node-security.yaml"),
      ("VPCStackTemplateURL", "eks-vpc.yaml"),
    ]:
      parameters[parameter_name] = self.upload_stack_template(template_name)

    return dict(
      StackName=self.eks_cluster_stack_name(cluster_name),
      TemplateURL=eks_cluster_stack_template_url,
      Parameters=[
        dict(
          ParameterKey=k,
          ParameterValue=v,
        )
        for (k, v) in parameters.items()
      ],
      Capabilities=[
        "CAPABILITY_IAM",
        "CAPABILITY_NAMED_IAM",
      ],
    )

  def create_eks_cluster_stack(
    self,
    cluster_name,
    system_node_config,
    cpu_node_config,
    gpu_node_config,
    key_name,
    kubernetes_version,
  ):
    kwargs = self.get_kwargs_for_cluster_stack(
      cluster_name=cluster_name,
      kubernetes_version=kubernetes_version,
      key_name=key_name,
      system_node_config=system_node_config,
      cpu_node_config=cpu_node_config,
      gpu_node_config=gpu_node_config,
    )
    return self.cloudformation.create_stack(**kwargs)

  def update_eks_cluster_stack(
    self,
    cluster_name,
    system_node_config,
    cpu_node_config,
    gpu_node_config,
    key_name,
    kubernetes_version,
    event_handler=None,
  ):
    try:
      stack = self.cloudformation.Stack(self.eks_cluster_stack_name(cluster_name))
    except botocore.exceptions.ClientError as ce:
      if ce.response["Error"]["Code"] == "ValidationError":
        raise Exception(f"The stack for cluster {cluster_name} does not exist") from ce
      raise
    last_event_before_update = self.client.describe_stack_events(StackName=stack.stack_id)["StackEvents"][0]
    kwargs = self.get_kwargs_for_cluster_stack(
      cluster_name=cluster_name,
      kubernetes_version=kubernetes_version,
      key_name=key_name,
      system_node_config=system_node_config,
      cpu_node_config=cpu_node_config,
      gpu_node_config=gpu_node_config,
      stack=stack,
    )
    self.client.update_stack(**kwargs)
    stack.reload()
    self.wait_for_stack_update_complete(
      stack.stack_id,
      event_handler=event_handler,
      after=last_event_before_update["Timestamp"],
    )
    stack.reload()
    return stack

  def delete_eks_cluster_stack(self, cluster_name):
    self.describe_eks_cluster_stack(cluster_name).delete()

  def describe_eks_cluster_stack(self, cluster_name):
    return self.cloudformation.Stack(self.eks_cluster_stack_name(cluster_name))

  def ensure_eks_cluster_stack(
    self,
    cluster_name,
    **kwargs,
  ):
    try:
      stack = self.create_eks_cluster_stack(
        cluster_name=cluster_name,
        **kwargs,
      )
    except self.client.exceptions.AlreadyExistsException:
      stack = self.describe_eks_cluster_stack(
        cluster_name=cluster_name,
      )

    stack.reload()
    return stack

  def get_stack_status(self, stack_name_or_id):
    stack = self.cloudformation.Stack(stack_name_or_id)
    return _call_boto_with_backoff(lambda: stack.stack_status)()

  # NOTE: if the stack was deleted then describe_stack_events raises a Throttling error.
  # We need to make sure a new error gets raised to indicate that the resource does not exist anymore.
  def _describe_stack_events_page(self, StackName, **kwargs):
    try:
      return self.client.describe_stack_events(StackName=StackName, **kwargs)
    except botocore.exceptions.ClientError as ce:
      try:
        stack_status = self.get_stack_status(StackName)
        if stack_status == "DELETE_COMPLETE":
          raise StackDeletedException("Stack deleted") from ce
        raise
      except botocore.exceptions.ClientError as e:
        raise ce from e

  def describe_stack_events(self, stack_name):
    params = {"StackName": stack_name}
    return self._page_boto(self._describe_stack_events_page, params, "StackEvents")

  def watch_stack_events(self, stack_name, event_handler, after=None, failures=None):
    stack_id = self.cloudformation.Stack(stack_name).stack_id
    event_counts = collections.defaultdict(int)
    all_stacks = [stack_id]
    initial_sleep_time = 1
    sleep_time = initial_sleep_time
    backoff_base = 1.1
    if failures is None:
      failures = []
    while all_stacks:
      for stack in all_stacks:
        stack_status = self.get_stack_status(stack)
        try:
          current_events = list(self.describe_stack_events(stack))
        except StackDeletedException:
          all_stacks.remove(stack)
          continue
        slice_end = len(current_events) - event_counts[stack]
        new_events = current_events[:slice_end][::-1]
        if new_events:
          sleep_time = initial_sleep_time
        event_counts[stack] = len(current_events)
        if event_handler:
          for event in new_events:
            if not after or event["Timestamp"] > after:
              event_handler(stack, event)
        for event in new_events:
          event_status = event["ResourceStatus"]
          if event_status.endswith("_FAILED"):
            failures.append(event)
          if event["ResourceType"] == "AWS::CloudFormation::Stack":
            resource_id = event.get("PhysicalResourceId")
            if not resource_id:
              continue
            if event_status.endswith("_IN_PROGRESS") and resource_id not in all_stacks:
              all_stacks.append(resource_id)
        if stack_status.endswith("_COMPLETE") or stack_status.endswith("_FAILED"):
          try:
            all_stacks.remove(stack)
          except ValueError:
            pass
      if all_stacks:
        time.sleep(sleep_time)
        sleep_time *= backoff_base
    return failures

  def _wait_for_stack_change_complete(self, stack_name, expected_status, event_handler=None, after=None):
    def maybe_raise_failures(failures, initial_exc):
      if failures:
        failures_str = "\n".join(
          f"{e['ResourceStatus']} {e['ResourceType']} {e['LogicalResourceId']}: {e['ResourceStatusReason']}"
          for e in failures
        )
        exc = Exception(f"Encountered failures while watching stack: {stack_name}\n{failures_str}")
        if initial_exc:
          raise exc from initial_exc
        raise exc
      if initial_exc:
        raise initial_exc

    failures = []
    try:
      self.watch_stack_events(stack_name, event_handler, after=after, failures=failures)
    except KeyboardInterrupt as ke:
      # NOTE: surface any creation errors with a keyboard interrupt,
      # since the user might have interrupted the command after observing resources being deleted
      maybe_raise_failures(failures, ke)
    maybe_raise_failures(failures, None)

    stack = self.cloudformation.Stack(stack_name)
    assert stack.stack_status == expected_status, f"Expected {expected_status}, got {stack.stack_status}"

  def wait_for_stack_create_complete(self, stack_name, **kwargs):
    return self._wait_for_stack_change_complete(stack_name, "CREATE_COMPLETE", **kwargs)

  def wait_for_stack_update_complete(self, stack_name, **kwargs):
    return self._wait_for_stack_change_complete(stack_name, "UPDATE_COMPLETE", **kwargs)

  def ensure_eks_cluster_stack_deleted(self, cluster_name, event_handler=None):
    self._ensure_stack_deleted(self.eks_cluster_stack_name(cluster_name), event_handler=event_handler)

  def _ensure_stack_deleted(self, stack_name, event_handler=None):
    stack = self.cloudformation.Stack(stack_name)
    try:
      stack.reload()
    except botocore.exceptions.ClientError as ce:
      if ce.response["Error"]["Code"] == "ValidationError":
        return
      raise

    after = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    stack.delete()
    self.watch_stack_events(stack.stack_id, event_handler, after=after)
    self.client.get_waiter("stack_delete_complete").wait(StackName=stack.stack_id)

  def get_stack_output(self, stack, output_key):
    outputs = stack.outputs
    if outputs is None:
      return None
    return next(o["OutputValue"] for o in outputs if o["OutputKey"] == output_key)

  def get_node_instance_role_arn(self, cluster_name):
    cluster_stack = self.describe_eks_cluster_stack(cluster_name)
    return self.get_stack_output(cluster_stack, "NodeInstanceRoleArn")
