import click

from ...arguments import dockerfile_option, project_option
from ..run_base import run_command
from .base import cluster_command


@cluster_command.command("test-run", context_settings=dict(
  allow_interspersed_args=False,
  ignore_unknown_options=True,
))
@click.pass_context
@dockerfile_option
@run_command
@project_option
def test_run(ctx, command, run_options, dockerfile, project):
  '''Start and debug a SigOpt Run on the connected Kubernetes cluster.'''
  ctx.obj.controller.test_run_on_cluster(
    command=command,
    run_options=run_options,
    dockerfile=dockerfile,
    project_id=project,
  )
