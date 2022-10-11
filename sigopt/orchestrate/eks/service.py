import boto3

from ..services.aws_base import AwsService


DEFAULT_KUBERNETES_VERSION = "1.23"
SUPPORTED_KUBERNETES_VERSIONS = ("1.20", "1.21", "1.22", "1.23")


class AwsEksService(AwsService):
  def __init__(self, services, aws_services, **kwargs):
    super().__init__(services, aws_services)
    self._client = boto3.client('eks', **kwargs)

  @property
  def client(self):
    return self._client

  def describe_cluster(self, cluster_name):
    return self.client.describe_cluster(name=cluster_name)
