# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import base64
import hashlib

import boto3

from ..services.aws_base import AwsService


class AwsS3Service(AwsService):
  def __init__(self, services, aws_services, **kwargs):
    super().__init__(services, aws_services)
    self._client = boto3.client("s3", **kwargs)
    self.region = boto3.session.Session().region_name
    self._init_kwargs = kwargs

  @property
  def client(self):
    return self._client

  @property
  def account_id(self):
    return boto3.client("sts", **self._init_kwargs).get_caller_identity()["Account"]

  @property
  def orchestrate_bucket_name(self):
    return f"sigopt.{self.account_id}"

  def ensure_orchestrate_bucket(self):
    create_bucket_params = dict(
      ACL="private",
      Bucket=self.orchestrate_bucket_name,
    )
    # NOTE: LocationConstraint is required for all regions but us-east-1.
    # In us-east-1 create_bucket will fail when LocationConstraint is provided.
    # https://github.com/boto/boto3/issues/125
    if self.region != "us-east-1":
      create_bucket_params["CreateBucketConfiguration"] = {"LocationConstraint": self.region}
    try:
      self.client.create_bucket(**create_bucket_params)
      self.client.put_bucket_encryption(
        Bucket=self.orchestrate_bucket_name,
        ServerSideEncryptionConfiguration={
          "Rules": [
            {
              "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256",
              },
              "BucketKeyEnabled": True,
            },
          ]
        },
      )
    except self.client.exceptions.BucketAlreadyOwnedByYou:
      pass
    return self.orchestrate_bucket_name

  def upload_resource_by_hash(self, path_prefix, package, resource_name):
    resource_content = self.services.resource_service.read(package, resource_name)
    md5_hash = hashlib.md5(resource_content)  # nosec
    md5_hex_hash = md5_hash.hexdigest()
    resource_path = f"orchestrate/resources/{path_prefix}/md5-{md5_hex_hash}/{resource_name}"
    md5_b64_hash = base64.b64encode(md5_hash.digest()).decode("ascii")
    bucket = self.ensure_orchestrate_bucket()
    self.client.put_object(
      Bucket=bucket,
      Key=resource_path,
      Body=resource_content,
      ContentMD5=md5_b64_hash,
    )
    return f"https://{bucket}.s3.amazonaws.com/{resource_path}"
