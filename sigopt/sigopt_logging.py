# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import sys
from logging import INFO, StreamHandler, getLogger


print_logger = getLogger("sigopt.print")
print_logger.setLevel(INFO)

stdout_handler = StreamHandler(stream=sys.stdout)


def enable_print_logging():
  global print_logger, stdout_handler
  print_logger.removeHandler(stdout_handler)
  print_logger.addHandler(stdout_handler)
