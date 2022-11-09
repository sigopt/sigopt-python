# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import errno
import hashlib
import os
import subprocess  # nosec
from urllib.request import urlretrieve

from sigopt.paths import get_bin_dir, get_executable_path

from .common import Platform, current_platform
from .exceptions import CheckExecutableError


def check_executable(command, sha256, full_check):
  exec_path = get_executable_path(command)
  try:
    if full_check:
      with open(exec_path, 'rb') as exec_fp:
        contents = exec_fp.read()
      file_sha256 = hashlib.sha256(contents).hexdigest()
    else:
      with open(f'{exec_path}.sha256', 'r') as exec_sha256_fp:
        file_sha256 = exec_sha256_fp.read()
  except IOError as e:
    if e.errno == errno.ENOENT:
      raise CheckExecutableError(f'Error opening the hash files for: {command}') from e
    raise

  if not sha256 == file_sha256:
    filetype = 'executable' if full_check else 'hash file'
    raise CheckExecutableError(
      f"the {filetype} for '{command}' does not have the expected hash"
    )

  if not os.access(exec_path, os.X_OK):
    raise CheckExecutableError(f"the file for '{command}' is not executable")

  if full_check:
    with open(os.devnull, 'w') as devnull:
      try:
        subprocess.check_call([exec_path], stdout=devnull, stderr=devnull)
        subprocess.check_call(
          [command],
          env={'PATH': get_bin_dir()},
          stdout=devnull,
          stderr=devnull,
        )
      except subprocess.CalledProcessError as e:
        raise CheckExecutableError(f'Exception checking the excecutable for {command}: {e}') from e
      except OSError as e:
        if e.errno == errno.ENOENT:
          raise CheckExecutableError(f'System cannot find executable for {command}') from e
        raise


KUBECTL_VERSION = 'v1.25.2'
KUBECTL_URL_FORMAT = 'https://dl.k8s.io/release/{}/bin/{}/amd64/kubectl'
KUBECTL_SHA256_LINUX = '8639f2b9c33d38910d706171ce3d25be9b19fc139d0e3d4627f38ce84f9040eb'
KUBECTL_SHA256_MAC = 'b859766d7b47267af5cc1ee01a2d0c3c137dbfc53cd5be066181beed11ec7d34'

AWS_IAM_AUTHENTICATOR_URL_FORMAT = (
  'https://github.com/kubernetes-sigs/aws-iam-authenticator/releases/download/v0.5.9/aws-iam-'
  'authenticator_0.5.9_{}_amd64'
)
AWS_IAM_AUTHENTICATOR_SHA256_LINUX = 'b192431c22d720c38adbf53b016c33ab17105944ee73b25f485aa52c9e9297a7'
AWS_IAM_AUTHENTICATOR_SHA256_MAC = '7656bd290a7e9cb588df1d9ccec43fab7f2447b88ed4f41d3f5092fd114b0939'

def check_kubectl_executable(full_check=False):
  check_executable(
    command='kubectl',
    sha256=(
      KUBECTL_SHA256_MAC
      if current_platform() == Platform.MAC
      else KUBECTL_SHA256_LINUX
    ),
    full_check=full_check,
  )

def check_iam_authenticator_executable(full_check=False):
  check_executable(
    command='aws-iam-authenticator',
    sha256=(
      AWS_IAM_AUTHENTICATOR_SHA256_MAC
      if current_platform() == Platform.MAC
      else AWS_IAM_AUTHENTICATOR_SHA256_LINUX
    ),
    full_check=full_check,
  )

def download_executable(command, url):
  executable_path = get_executable_path(command)
  urlretrieve(url, executable_path)  # nosec
  os.chmod(executable_path, 0o700)
  with \
    open(executable_path, 'rb') as exec_fp, \
    open(f'{executable_path}.sha256', 'w') as sha256_fp:
    sha256_fp.write(hashlib.sha256(exec_fp.read()).hexdigest())

def download_kubectl_executable():
  download_executable(
    'kubectl',
    KUBECTL_URL_FORMAT.format(
      KUBECTL_VERSION,
      ('darwin' if current_platform() == Platform.MAC else 'linux'),
    )
  )

def download_iam_authenticator_executable():
  download_executable(
    'aws-iam-authenticator',
    AWS_IAM_AUTHENTICATOR_URL_FORMAT.format(
      ('darwin' if current_platform() == Platform.MAC else 'linux'),
    )
  )
