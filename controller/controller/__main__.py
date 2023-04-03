# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import logging
import os

from controller.manage_pods import ExperimentPodsManager, RunPodsManager


def main():
  mode = os.environ["CONTROLLER_MODE"]
  if mode == "run":
    manager_cls = RunPodsManager
  elif mode == "experiment":
    manager_cls = ExperimentPodsManager
  manager = manager_cls.from_env()
  manager.start()


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  main()
