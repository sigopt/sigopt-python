# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import os

from sigopt.paths import get_bin_dir

from ..paths import get_executable_path
from ..services.base import Service


class KubectlService(Service):
  def get_kubectl_command(self):
    return get_executable_path('kubectl')

  def get_kubectl_env(self):
    kube_config = self.get_kube_config()
    assert kube_config, "The kubectl service has no kubernetes config"
    orchestrate_bin = get_bin_dir()
    env = os.environ.copy()
    previous_path = env.get('PATH', '')
    env.update(dict(
      KUBECONFIG=kube_config,
      PATH=f'{orchestrate_bin}:{previous_path}'.encode(),
    ))
    return env

  @property
  def get_kube_config(self):
    return self.services.kubernetes_service.kube_config
