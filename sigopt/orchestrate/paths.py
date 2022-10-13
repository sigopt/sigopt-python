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


KUBECTL_VERSION = 'v1.20.4'
KUBECTL_URL_FORMAT = 'https://storage.googleapis.com/kubernetes-release/release/{}/bin/{}/amd64/kubectl'
KUBECTL_SHA256_LINUX = '98e8aea149b00f653beeb53d4bd27edda9e73b48fed156c4a0aa1dabe4b1794c'
KUBECTL_SHA256_MAC = '37f593731b8c9913bf2a3bfa36dacb3058dc176c7aeae2930c783822ea03a573'

AWS_IAM_AUTHENTICATOR_URL_FORMAT = (
  'https://github.com/kubernetes-sigs/aws-iam-authenticator/releases/download/0.4.0-alpha.1/aws-iam-'
  'authenticator_0.4.0-alpha.1_{}_amd64'
)
AWS_IAM_AUTHENTICATOR_SHA256_LINUX = 'a573503724b15857e4c766fb16b7992865f34715a5297e46a046af9536ccb71a'
AWS_IAM_AUTHENTICATOR_SHA256_MAC = 'e98beb32cd15c198dedd9da46bd56599ee36e0e9e6debede4bd737a8158da92a'

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
