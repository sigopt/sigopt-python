# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from ...arguments import dockerfile_option, project_option
from ..optimize_base import optimize_command
from .base import cluster_command


@cluster_command.command(
  context_settings=dict(
    allow_interspersed_args=False,
    ignore_unknown_options=True,
  )
)
@click.pass_context
@dockerfile_option
@optimize_command
@project_option
def optimize(ctx, command, run_options, experiment_file, dockerfile, project):
  """Run an Experiment on the connected Kubernetes cluster."""
  ctx.obj.controller.optimize_on_cluster(
    command=command,
    run_options=run_options,
    optimization_options=experiment_file.data,
    silent=False,
    dockerfile=dockerfile,
    project_id=project,
  )
