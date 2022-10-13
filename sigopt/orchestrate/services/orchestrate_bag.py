# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from ..cluster.service import ClusterService
from ..cluster_metadata.service import ClusterMetadataService
from ..gpu_options_validator.service import GpuOptionsValidatorService
from ..job_runner.service import JobRunnerService
from ..job_status.service import JobStatusService
from ..kubectl.service import KubectlService
from ..kubernetes.service import KubernetesService
from ..logging.service import LoggingService
from ..model_packer.service import ModelPackerService
from ..options_validator.service import OptionsValidatorService
from ..provider.broker import ProviderBroker
from ..resource.service import ResourceService
from ..sigopt.service import SigOptService
from .bag import ServiceBag


class OrchestrateServiceBag(ServiceBag):
  def _create_services(self):
    super()._create_services()
    self.resource_service = ResourceService(self)
    self.provider_broker = ProviderBroker(self)
    self.cluster_metadata_service = ClusterMetadataService(self)
    self.cluster_service = ClusterService(self)
    self.job_runner_service = JobRunnerService(self)
    self.job_status_service = JobStatusService(self)
    self.kubectl_service = KubectlService(self)
    self.kubernetes_service = KubernetesService(self)
    self.logging_service = LoggingService(self)
    self.model_packer_service = ModelPackerService(self)
    self.options_validator_service = OptionsValidatorService(self)
    self.gpu_options_validator_service = GpuOptionsValidatorService(self)
    self.sigopt_service = SigOptService(self)

  def _warmup_services(self):
    super()._warmup_services()
    self.kubernetes_service.warmup()
