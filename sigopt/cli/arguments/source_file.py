# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click


def file_contents(ctx, param, value):  # pylint: disable=unused-argument
  if value is None:
    return None
  with open(value, "r") as fp:
    return fp.read()


source_file_option = click.option(
  "-s",
  "--source-file",
  type=click.Path(exists=True),
  callback=file_contents,
  help="A file containing the source code for your run. The contents will be stored as data on your run.",
)
