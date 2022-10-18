# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
class K8sEvent:
  DELETED = "DELETED"
  MODIFIED = "MODIFIED"

class K8sPhase:
  PENDING = "Pending"
  RUNNING = "Running"
  SUCCEEDED = "Succeeded"
  FAILED = "Failed"
