# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import os

from sigopt.paths import get_bin_dir

from ..exceptions import OrchestrateException
from ..services.base import Service


class KubectlError(OrchestrateException):
  def __init__(self, args, return_code, stdout, stderr):
    super().__init__()
    self.args = args
    self.return_code = return_code
    self.stdout = stdout.read()
    self.stderr = stderr.read()

  def __str__(self):
    return (
      f'kubectl command {self.args} failed with exit status {self.return_code}\n'
      f'stdout:\n{self.stdout}\nstderr:\n{self.stderr}'
    )

class KubectlService(Service):
  kubectl_command = 'kubectl'

  def kubectl_env(self):
    assert self.kube_config, "The kubectl service has no kubernetes config"
    orchestrate_bin = get_bin_dir()
    env = os.environ.copy()
    previous_path = env.get('PATH', '')
    env.update(dict(
      KUBECONFIG=self.kube_config,
      PATH=f'{orchestrate_bin}:{previous_path}'.encode(),
    ))
    return env

  @property
  def kube_config(self):
    return self.services.kubernetes_service.kube_config
