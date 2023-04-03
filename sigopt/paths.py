# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import errno
import os


def get_root_dir():
  root_dir = os.environ.get("SIGOPT_HOME", os.path.join("~", ".sigopt"))
  return os.path.expanduser(root_dir)


def get_root_subdir(dirname):
  return os.path.join(get_root_dir(), dirname)


def get_bin_dir():
  return get_root_subdir("bin")


def ensure_dir(path):
  try:
    os.makedirs(path)
  except os.error as oserr:
    if oserr.errno != errno.EEXIST:
      raise


def get_executable_path(command):
  return os.path.join(get_bin_dir(), command)
