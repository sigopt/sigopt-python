from ..lib.types import is_boolean, is_integer, is_mapping, is_sequence, is_string
from ..node_groups import ALL_NODE_GROUP_TYPES, NODE_GROUP_TYPE_CPU, NODE_GROUP_TYPE_GPU, NODE_GROUP_TYPE_SYSTEM
from ..services.base import Service


class OptionsValidatorService(Service):
  def validate_resources_per_model(self, gpus=None, requests=None, limits=None):
    if gpus is not None:
      assert is_integer(gpus) and gpus >= 0, f'resources_per_model.gpus is not a non-negative integer: {gpus}'
    if requests is not None:
      assert is_mapping(requests), f'resources_per_model.requests is not a mapping: {requests}'
    if limits is not None:
      assert is_mapping(limits), f'resources_per_model.limits is not a mapping: {limits}'

  def validate_aws_for_orchestrate(
    self,
    aws_access_key_id=None,
    aws_secret_access_key=None,
  ):
    self.validate_aws_keys(
      aws_access_key_id=aws_access_key_id,
      aws_secret_access_key=aws_secret_access_key
    )

  def validate_aws_for_cluster(
    self,
    aws_access_key_id=None,
    aws_secret_access_key=None,
    additional_policies=None,
  ):
    self.validate_aws_keys(
      aws_access_key_id=aws_access_key_id,
      aws_secret_access_key=aws_secret_access_key
    )

    if additional_policies:
      assert is_sequence(additional_policies), f'aws.additional_policies is not a list: {additional_policies}'

  def validate_aws_keys(
    self,
    aws_access_key_id=None,
    aws_secret_access_key=None,
  ):
    if aws_secret_access_key is not None:
      assert is_string(aws_secret_access_key) and aws_secret_access_key, (
        f'Please provide a string aws.aws_secret_access_key: {aws_secret_access_key}'
      )
    if aws_access_key_id is not None:
      assert is_string(aws_access_key_id) and aws_access_key_id, (
        f'Please provide a string aws.aws_access_key_id: {aws_access_key_id}'
      )

  def validate_sigopt(self, api_token=None, verify_ssl_certs=None):
    if api_token is not None:
      assert is_string(api_token) and api_token, (
        f'Please provide a string sigopt.api_token: {api_token}'
      )
    if verify_ssl_certs is not None:
      assert (
        is_boolean(verify_ssl_certs) or (is_string(verify_ssl_certs) and verify_ssl_certs)
      ), (
        f'Please provide a boolean or string sigopt.verify_ssl_certs: {verify_ssl_certs}'
      )

  def validate_cluster_options(
    self,
    provider=None,
    cluster_name=None,
    aws=None,
    kubernetes_version=None,
    **kwargs,
  ):
    unknown_options = set(kwargs) - ALL_NODE_GROUP_TYPES
    assert not unknown_options, f"Unknown options provided: {', '.join(unknown_options)}"
    assert provider and is_string(provider), (
      f'We need a string `provider` to create your cluster: {provider}'
    )

    if aws is not None:
      self.validate_aws_for_cluster(**aws)

    if kubernetes_version is not None:
      assert is_string(kubernetes_version), "kubernetes_version should have a string value"

    assert is_string(cluster_name) and cluster_name, 'We need a string `cluster_name` to create your cluster'
    assert kwargs.get(NODE_GROUP_TYPE_CPU) or kwargs.get(NODE_GROUP_TYPE_GPU), (
      'Please specify some cpu or gpu (or both) nodes for your cluster'
    )
    for node_group_type in ALL_NODE_GROUP_TYPES:
      node_group_options = kwargs.get(node_group_type)
      if not node_group_options:
        continue
      assert is_mapping(node_group_options), f"{node_group_type} is not a mapping: {node_group_options}"
      self.validate_worker_stack(name=node_group_type, **node_group_options)

  def validate_worker_stack(
    self,
    name,
    instance_type=None,
    max_nodes=None,
    min_nodes=None,
    node_volume_size=None,
  ):
    if name != NODE_GROUP_TYPE_SYSTEM:
      assert instance_type is not None, f'Missing: {name}.instance_type'
      assert max_nodes is not None, f'Missing: {name}.max_nodes (can be the same as {name}.min_nodes)'
      assert min_nodes is not None, f'Missing: {name}.min_nodes (can be the same as {name}.max_nodes)'

    if instance_type is not None:
      assert is_string(instance_type), f'{name}.instance_type is not a string: {instance_type}'

    if max_nodes is not None:
      assert is_integer(max_nodes) and max_nodes > 0, f'{name}.max_nodes is not a positive integer: {max_nodes}'

    if min_nodes is not None:
      assert is_integer(min_nodes) and min_nodes >= 0, f'{name}.min_nodes is not a non-negative integer: {min_nodes}'

    if node_volume_size is not None:
      assert is_integer(node_volume_size) and node_volume_size > 0, (
        f'{name}.node_volume_size is not a positive integer: {node_volume_size}'
      )
