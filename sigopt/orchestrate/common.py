# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import secrets
import sys
import time
from enum import Enum
from shutil import rmtree
from tempfile import mkdtemp


class TemporaryDirectory(object):
  def __init__(self, *args, **kwargs):
    self.directory = mkdtemp(*args, **kwargs)

  def __enter__(self):
    return self.directory

  def __exit__(self, *args):
    rmtree(self.directory)


class Platform(Enum):
  MAC = 1
  LINUX = 2


def current_platform():
  if sys.platform.startswith("linux"):
    return Platform.LINUX
  if sys.platform == "darwin":
    return Platform.MAC
  raise Exception(
    "You are attempting to run SigOpt cluster features on the following platform:"
    f" {sys.platform}. Currently, only Mac and Linux are supported."
  )


def retry_with_backoff(func):
  # pylint: disable=inconsistent-return-statements
  def wrapper(*args, **kwargs):
    NUM_RETRIES = 5
    for i in range(NUM_RETRIES + 1):
      try:
        return func(*args, **kwargs)
      except Exception as e:
        time.sleep(2**i + secrets.SystemRandom().random())  # nosec
        if i == NUM_RETRIES:
          raise e

  # pylint: enable=inconsistent-return-statements
  return wrapper
