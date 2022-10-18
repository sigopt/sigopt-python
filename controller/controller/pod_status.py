# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from controller.k8s_constants import K8sPhase


def is_pod_phase_active(pod_phase):
  return pod_phase in (K8sPhase.PENDING, K8sPhase.RUNNING)

def is_pod_phase_finished(pod_phase):
  return pod_phase in (K8sPhase.SUCCEEDED, K8sPhase.FAILED)

def is_pod_active(pod):
  return is_pod_phase_active(pod.status.phase)

def is_pod_finished(pod):
  return is_pod_phase_finished(pod.status.phase)
