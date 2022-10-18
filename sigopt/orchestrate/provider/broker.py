# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from ..aws.service import AwsService
from ..custom_cluster.service import CustomClusterService
from ..provider.constants import Provider
from ..services.aws_provider_bag import AwsProviderServiceBag
from ..services.base import Service


class ProviderBroker(Service):
  def get_provider_service(self, provider):
    if provider == Provider.AWS:
      return AwsService(self.services, AwsProviderServiceBag(self.services))
    if provider == Provider.CUSTOM:
      return CustomClusterService(self.services)
    raise NotImplementedError()
