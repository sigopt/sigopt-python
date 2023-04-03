# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import pytest
from mock import Mock

from sigopt.orchestrate.job_runner.service import JobRunnerService
from sigopt.orchestrate.resource.service import ResourceService


class TestJobRunnerService(object):
  @pytest.fixture
  def services(self):
    services = Mock(sigopt_service=Mock(api_token="sigopt_api_token"))
    services.resource_service = ResourceService(services)
    return services

  @pytest.fixture
  def job_runner_service(self, services):
    return JobRunnerService(services)

  @pytest.mark.parametrize(
    "resources,expected_output",
    [
      (
        dict(requests={"cpu": 5}),
        dict(
          requests={
            "cpu": 5,
            "ephemeral-storage": JobRunnerService.DEFAULT_EPHEMERAL_STORAGE_REQUEST,
          },
          limits={},
        ),
      ),
      (
        dict(requests={"cpu": "300m"}, gpus=1),
        dict(
          requests={
            "cpu": "300m",
            "ephemeral-storage": JobRunnerService.DEFAULT_EPHEMERAL_STORAGE_REQUEST,
          },
          limits={"nvidia.com/gpu": 1},
        ),
      ),
      (
        dict(requests={"cpu": "1"}, limits={"memory": "2Gi", "cpu": 2}, gpus=1),
        dict(
          requests={
            "cpu": "1",
            "ephemeral-storage": JobRunnerService.DEFAULT_EPHEMERAL_STORAGE_REQUEST,
          },
          limits={
            "memory": "2Gi",
            "cpu": 2,
            "nvidia.com/gpu": 1,
          },
        ),
      ),
      (
        dict(
          requests={"cpu": "1", "ephemeral-storage": "1Ti"},
          limits={"memory": "2Gi", "cpu": 2},
          gpus=1,
        ),
        dict(
          requests={"cpu": "1", "ephemeral-storage": "1Ti"},
          limits={
            "memory": "2Gi",
            "cpu": 2,
            "nvidia.com/gpu": 1,
          },
        ),
      ),
    ],
  )
  def test_format_resources(self, job_runner_service, resources, expected_output):
    job_runner_service.format_resources(resources)
    assert resources == expected_output
