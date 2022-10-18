# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from .version import CLI_NAME


class OrchestrateException(click.ClickException):
  def __init__(self, msg=None):
    if msg is None:
      msg = f"Uncaught exception: {type(self).__name__}"
    super().__init__(msg)

class CheckExecutableError(OrchestrateException):
  pass

class CheckConnectionError(OrchestrateException):
  pass

class AwsClusterSharePermissionError(OrchestrateException):
  pass

class AwsPermissionsError(OrchestrateException):
  def __init__(self, error):
    super().__init__(
      "Looks like you have encountered the below AWS permissions error."
      " Please check out our documentation and ensure you have granted yourself the correct AWS permissions"
      " to use SigOpt cluster features:"
      " https://app.sigopt.com/docs/orchestrate/deep_dive#aws_permissions"
      f"\n\n{error}"
    )

class MissingGpuNodesException(OrchestrateException):
  pass

class ModelPackingError(OrchestrateException):
  def __init__(self, error_str, dockerfile):
    super().__init__(
      f'{error_str}\n'
      f'Dockerfile: {dockerfile}\n'
      f'If you suspect that you are out of space, run `{CLI_NAME} clean` and try again.',
    )

class ClusterDestroyError(OrchestrateException):
  def __init__(self):
    print('The following exceptions occurred during cluster destroy:\n')
    super().__init__()

class NodesNotReadyError(OrchestrateException):
  pass

class FileAlreadyExistsError(OrchestrateException):
  def __init__(self, filename):
    self.filename = filename

    super().__init__(
      f'We are attempting to write a file, but it already exists on your system: {filename}.'
      ' Please delete the file and try your request again.'
    )
