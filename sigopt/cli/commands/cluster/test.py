# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from .base import cluster_command


@cluster_command.command()
@click.pass_context
def test(ctx):
  '''Test the connection to the connected Kubernetes cluster.'''
  ctx.obj.controller.test_cluster_connection()
