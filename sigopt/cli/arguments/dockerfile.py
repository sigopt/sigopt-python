# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click


dockerfile_option = click.option(
  "-d",
  "--dockerfile",
  type=click.Path(exists=True),
  default="./Dockerfile",
)
