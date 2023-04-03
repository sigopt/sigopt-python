# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import boto3

from ..services.aws_base import AwsService


class AwsEcrService(AwsService):
  def __init__(self, services, aws_services, **kwargs):
    super().__init__(services, aws_services)
    self._client = boto3.client("ecr", **kwargs)

  @property
  def client(self):
    return self._client

  def _create_repository(self, repository_name):
    return self.client.create_repository(repositoryName=repository_name)

  def _describe_repositories(self, repository_names):
    return self.client.describe_repositories(repositoryNames=repository_names)

  def ensure_repositories(self, repository_names):
    for name in repository_names:
      try:
        self._create_repository(repository_name=name)
      except self.client.exceptions.RepositoryAlreadyExistsException:
        pass

    return self._describe_repositories(repository_names)

  def get_authorization_token(self, registry_ids):
    return self.client.get_authorization_token(registryIds=registry_ids)
