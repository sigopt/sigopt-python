# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import click

from sigopt.orchestrate.provider.constants import Provider, provider_to_string
from sigopt.validate import validate_top_level_dict

from ...arguments import cluster_name_option, load_yaml_callback, provider_option
from .base import cluster_command


@cluster_command.command()
@cluster_name_option
@provider_option
@click.option(
  '--kubeconfig',
  type=click.Path(exists=True),
  callback=load_yaml_callback(validate_top_level_dict),
  help='A kubeconfig used to connect to this cluster',
)
@click.option('--registry', help='A custom image registry (host[:port][/path])')
@click.pass_context
def connect(ctx, cluster_name, provider, kubeconfig, registry):
  '''Connect to an existing Kubernetes cluster.'''
  if kubeconfig and provider != provider_to_string(Provider.CUSTOM):
    raise click.BadParameter("Only --provider=custom is allowed with --kubeconfig")
  ctx.obj.controller.connect_to_cluster(cluster_name, provider, registry, kubeconfig and kubeconfig.data)
