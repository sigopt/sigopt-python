# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import pytest
from mock import Mock

from sigopt.orchestrate.aws.service import AwsService, is_cuda_gpu_instance_type


class TestAwsService(object):
  @pytest.fixture()
  def aws_service(self):
    services = Mock()
    aws_services = Mock()
    return AwsService(services, aws_services)

  def test_gpu_instance_type(self):
    assert is_cuda_gpu_instance_type('p4d.24xlarge')
    assert is_cuda_gpu_instance_type('p3.2xlarge')
    assert is_cuda_gpu_instance_type('p3dn.24xlarge')
    assert is_cuda_gpu_instance_type('p2.16xlarge')
    assert is_cuda_gpu_instance_type('g4dn.xlarge')
    assert is_cuda_gpu_instance_type('g4dn.metal')
    assert is_cuda_gpu_instance_type('g3.16xlarge')

    assert not is_cuda_gpu_instance_type('g4ad.16xlarge')
    assert not is_cuda_gpu_instance_type('f1.16xlarge')
    assert not is_cuda_gpu_instance_type('c5.24xlarge')
    assert not is_cuda_gpu_instance_type('t2.small')

  @pytest.fixture
  def cpu_config(self):
    return {"min_size": 1, "max_size": 2, "instance_type": "m5.large"}

  @pytest.fixture
  def gpu_config(self):
    return {"min_size": 1, "max_size": 2, "instance_type": "p3.2xlarge"}

  @pytest.mark.parametrize('cluster_name', [
    '',
    'inval_id1-123',
    'also-invalid_cluster-name',
    '123',
  ])
  def test_invalid_cluster_name(self, aws_service, cluster_name, cpu_config, gpu_config):
    with pytest.raises(AssertionError):
      aws_service.validate_cluster_options(cluster_name, {"cpu": cpu_config, "gpu": gpu_config}, None)

  @pytest.mark.parametrize('cluster_name', [
    'valid-123',
    'also-valid-cluster-name',
  ])
  def test_valid_cluster_names(self, aws_service, cluster_name, cpu_config, gpu_config):
    aws_service.validate_cluster_options(cluster_name, {"cpu": cpu_config, "gpu": gpu_config}, None)

  @pytest.mark.parametrize('kubernetes_version', [
    '1.9',
    '1.15',
    'not-a-version',
  ])
  def test_invalid_kubernetes_version(self, aws_service, kubernetes_version, cpu_config, gpu_config):
    with pytest.raises(AssertionError):
      aws_service.validate_cluster_options('cluster-name', {"cpu": cpu_config, "gpu": gpu_config}, kubernetes_version)

  @pytest.mark.parametrize('kubernetes_version', [
    None,
    '1.20',
    '1.23',
    'latest',
  ])
  def test_valid_kubernetes_versions(self, aws_service, kubernetes_version, cpu_config, gpu_config):
    aws_service.validate_cluster_options('valid-name', {"cpu": cpu_config, "gpu": gpu_config}, kubernetes_version)

  def test_create_kubernetes_cluster_fail(self, aws_service, cpu_config, gpu_config):
    with pytest.raises(AssertionError):
      aws_service.create_kubernetes_cluster(dict(cluster_name="44_44", cpu=cpu_config, gpu=gpu_config))
