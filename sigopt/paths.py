# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import os


def get_root_dir():
  root_dir = os.environ.get("SIGOPT_HOME", os.path.join("~", ".sigopt"))
  return os.path.expanduser(root_dir)


def get_root_subdir(dirname):
  return os.path.join(get_root_dir(), dirname)
