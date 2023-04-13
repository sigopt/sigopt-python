# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import errno
import os

import boto3
from botocore.exceptions import ClientError

from sigopt.paths import ensure_dir, get_root_subdir

from ..services.aws_base import AwsService


class AwsEc2Service(AwsService):
  def __init__(self, services, aws_services, **kwargs):
    super().__init__(services, aws_services)
    self._ec2 = boto3.resource("ec2", **kwargs)

  @property
  def ec2(self):
    return self._ec2

  def get_subnets(self, subnet_ids):
    subnets = self.ec2.subnets.all()
    return list(subnet for subnet in subnets if subnet.id in subnet_ids)

  def key_pair_for_cluster_name(self, cluster_name):
    return f"key-pair-for-cluster-{cluster_name}"

  def describe_key_pair_for_cluster(self, cluster_name):
    return self.ec2.KeyPair(self.key_pair_for_cluster_name(cluster_name))

  def create_key_pair_for_cluster(self, cluster_name):
    key_pair = self.ec2.create_key_pair(KeyName=self.key_pair_for_cluster_name(cluster_name))

    self.ensure_key_pair_directory()

    try:
      with os.fdopen(
        os.open(self.key_pair_location(cluster_name), os.O_CREAT | os.O_WRONLY, 0o600),
        "w",
      ) as f:
        f.write(key_pair.key_material)
    except Exception:
      # We only get one chance to read the key, so if we mess up then delete the key so we can try again next time
      key_pair.delete()
      raise

    return key_pair

  def ensure_key_pair_for_cluster(self, cluster_name):
    try:
      self.create_key_pair_for_cluster(cluster_name)
    except ClientError as e:
      if not e.response["Error"]["Code"] == "InvalidKeyPair.Duplicate":
        raise e

    return self.describe_key_pair_for_cluster(cluster_name)

  def delete_key_pair_for_cluster(self, cluster_name):
    try:
      os.remove(self.key_pair_location(cluster_name))
    except OSError as e:
      if e.errno != errno.ENOENT:
        raise

    self.describe_key_pair_for_cluster(cluster_name).delete()

  @property
  def key_pair_directory(self):
    return get_root_subdir("ssh")

  def ensure_key_pair_directory(self):
    ensure_dir(self.key_pair_directory)

  def key_pair_location(self, cluster_name):
    key_name = self.key_pair_for_cluster_name(cluster_name)
    filename = f"{key_name}.pem"
    return os.path.join(self.key_pair_directory, filename)

  def ensure_key_pair_for_cluster_deleted(self, cluster_name):
    # Note: under our current structure, no error occurs if we attempt to
    # delete a non-existent keypair
    self.delete_key_pair_for_cluster(cluster_name)
