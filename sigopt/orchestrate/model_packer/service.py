# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import os
import shutil
import shlex

from sigopt.config import config as sigopt_config

from ..common import TemporaryDirectory
from ..services.base import Service


def create_model_packer_dockerfile(
  base_image,
  verify_ssl_certs,
  no_verify_ssl_certs,
  sigopt_home,
):
  lines = []
  lines.append(f"FROM {shlex.quote(base_image)}")
  lines.append("LABEL orchestrate-user-created=true")
  lines.append("COPY . /")
  if verify_ssl_certs:
    lines.append(f"ENV SIGOPT_API_VERIFY_SSL_CERTS {shlex.quote(verify_ssl_certs)}")
  if no_verify_ssl_certs:
    lines.append(f"ENV SIGOPT_API_NO_VERIFY_SSL_CERTS {shlex.quote(no_verify_ssl_certs)}")
  if sigopt_home:
    lines.append(f"ENV SIGOPT_HOME {shlex.quote(sigopt_home)}")
  return "".join(f"{l}\n" for l in lines)

class ModelPackerService(Service):
  def build_image(
    self,
    docker_service,
    repository,
    tag,
    quiet=False,
    dockerfile=None,
  ):
    if not os.path.isfile(dockerfile):
      raise Exception('Please specify a path to a Dockerfile')

    with open(dockerfile) as dockerfile_fp:
      dockerfile_contents = dockerfile_fp.read()
      cwd = os.getcwd()

      user_image_tag = docker_service.build(
        directory=cwd,
        dockerfile_contents=dockerfile_contents,
        quiet=quiet,
        show_all_logs=True,
      )

    try:
      with TemporaryDirectory() as root_dirname:
        ssl_dirname = os.path.join(root_dirname, 'etc', 'ssl')
        sigopt_config_dirname = os.path.join(root_dirname, 'etc', 'sigopt', 'client')
        for dirname in (ssl_dirname, sigopt_config_dirname):
          os.makedirs(dirname)

        verify_ssl_certs = None
        no_verify_ssl_certs = None
        local_verify_ssl_certs = self.services.sigopt_service.verify_ssl_certs
        # NOTE(dan): we intentionally leave verify_ssl_certs as None in the bool/True case because
        # verify_ssl_certs must refer to a file when being passed as an environment variable
        if isinstance(local_verify_ssl_certs, bool):
          no_verify_ssl_certs = not local_verify_ssl_certs
        elif local_verify_ssl_certs is not None:
          build_context_verify_ssl_certs = os.path.join(ssl_dirname, 'sigopt-ca.crt')
          shutil.copyfile(local_verify_ssl_certs, build_context_verify_ssl_certs)
          verify_ssl_certs = build_context_verify_ssl_certs.replace(root_dirname, '/')

        sigopt_home = None
        local_config_path = sigopt_config.config_json_path
        if local_config_path is not None and os.path.exists(local_config_path):
          build_context_config_path = os.path.join(sigopt_config_dirname, 'config.json')
          shutil.copyfile(local_config_path, build_context_config_path)
          sigopt_home = os.path.dirname(os.path.dirname(build_context_config_path.replace(root_dirname, '/')))

        return docker_service.build(
          tag=docker_service.format_image_name(repository, tag),
          directory=root_dirname,
          dockerfile_contents=create_model_packer_dockerfile(
            base_image=user_image_tag,
            verify_ssl_certs=verify_ssl_certs,
            no_verify_ssl_certs=no_verify_ssl_certs,
            sigopt_home=sigopt_home,
          ),
          quiet=quiet,
          show_all_logs=False,
        )
    finally:
      docker_service.remove_tag(user_image_tag)
