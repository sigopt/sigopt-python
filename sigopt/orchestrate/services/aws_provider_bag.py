# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from ..cloudformation.service import AwsCloudFormationService
from ..ec2.service import AwsEc2Service
from ..ecr.service import AwsEcrService
from ..eks.service import AwsEksService
from ..iam.service import AwsIamService
from ..s3.service import AwsS3Service
from ..services.bag import ServiceBag
from ..sts.service import AwsStsService


class AwsProviderServiceBag(ServiceBag):
  def __init__(self, orchestrate_services):
    self.orchestrate_services = orchestrate_services
    super().__init__()

  def _create_services(self):
    super()._create_services()
    self.cloudformation_service = AwsCloudFormationService(self.orchestrate_services, self)
    self.ec2_service = AwsEc2Service(self.orchestrate_services, self)
    self.ecr_service = AwsEcrService(self.orchestrate_services, self)
    self.eks_service = AwsEksService(self.orchestrate_services, self)
    self.iam_service = AwsIamService(self.orchestrate_services, self)
    self.sts_service = AwsStsService(self.orchestrate_services, self)
    self.s3_service = AwsS3Service(self.orchestrate_services, self)
