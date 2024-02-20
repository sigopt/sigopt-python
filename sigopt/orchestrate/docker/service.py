# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import re
import secrets
import string
import sys
from collections import namedtuple
from tempfile import NamedTemporaryFile

import docker
import requests
import urllib3

from ..exceptions import ModelPackingError, OrchestrateException
from ..json_stream import json_stream
from ..services.base import Service


DOCKER_TARGET_VERSION = "1.41"


DockerLoginCredentials = namedtuple(
  "DockerLoginCredentials",
  [
    "username",
    "password",
    "registry",
  ],
)


class DockerException(OrchestrateException):
  pass


class DockerInstallationError(DockerException):
  pass


class DockerPodTimeoutError(DockerException):
  pass


class DockerConnectionError(DockerException):
  pass


class DockerService(Service):
  @classmethod
  def create(cls, services):
    if not services.kubernetes_service.is_docker_installed():
      raise DockerInstallationError(
        "\n".join(
          [
            "Docker not found in your cluster.",
            "SigOpt no longer uses your local Docker installation to build images.",
            "Please install the SigOpt plugins to get Docker running on your cluster:",
            "\tsigopt cluster install-plugins",
          ]
        )
      )
    try:
      services.kubernetes_service.wait_for_docker_pod()
    except TimeoutError as e:
      raise DockerPodTimeoutError(str(e)) from e
    client = docker.DockerClient(
      # HACK: DockerClient can't accept the kubernetes proxy url if it doesn't have a port specified, so give it
      # a fake url to initialize
      base_url="tcp://a:1",
      version=DOCKER_TARGET_VERSION,
    )
    services.kubernetes_service.mount_http_proxy_adapter(client.api)
    client.api.base_url = services.kubernetes_service.get_docker_connection_url()
    return cls(services, client)

  def __init__(self, services, client):
    super().__init__(services)
    self.client = client

  def check_connection(self):
    try:
      self.client.images.list()
    except (docker.errors.DockerException, requests.exceptions.ConnectionError) as e:
      raise DockerConnectionError(f"An error occurred while checking your docker connection: {e}") from e

  def print_logs(self, logs):
    for log in logs:
      sys.stdout.write(log)
      sys.stdout.flush()

  def stream_build_log(self, logs, dockerfile, show_all_logs):
    downloading = False
    for parsed_log in json_stream(logs):
      if "error" in parsed_log:
        if show_all_logs:
          print(parsed_log["error"], file=sys.stderr)
        raise ModelPackingError(parsed_log["error"], dockerfile)
      if "status" in parsed_log:
        if not downloading and parsed_log["status"] == "Downloading":
          yield "Downloading the base image...\n"
          downloading = True
      elif "stream" in parsed_log:
        if show_all_logs:
          yield parsed_log["stream"]
        downloading = False

  def build(
    self,
    tag=None,
    dockerfile_name=None,
    dockerfile_contents=None,
    directory=None,
    quiet=True,
    build_args=None,
    show_all_logs=False,
  ):
    if dockerfile_contents:
      assert not dockerfile_name, "only one of dockerfile_name, dockerfile_contents can be provided"
      with NamedTemporaryFile(mode="w", delete=False) as dockerfile_fp:
        dockerfile_fp.write(dockerfile_contents)
        dockerfile = dockerfile_fp.name
    else:
      dockerfile = dockerfile_name
    try:
      tag = tag or (
        "sigopt-temp:"
        + "".join(secrets.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(8))  # nosec
      )
      if quiet:
        self.client.images.build(
          tag=tag,
          dockerfile=dockerfile,
          path=directory,
          quiet=quiet,
          buildargs=build_args,
          rm=True,
        )
        return tag
      raw_logs = self.client.api.build(
        tag=tag,
        dockerfile=dockerfile,
        path=directory,
        quiet=quiet,
        buildargs=build_args,
        rm=True,
      )
      self.print_logs(self.stream_build_log(raw_logs, dockerfile, show_all_logs))
      return tag
    except docker.errors.BuildError as e:
      raise ModelPackingError(str(e), dockerfile) from e

  def push(self, repository, tag=None, retries=1, quiet=True):
    for try_number in range(retries + 1):
      try:
        for obj in json_stream(self.client.images.push(repository=repository, tag=tag, stream=True)):
          if "error" in obj:
            raise Exception(obj["error"])
      except urllib3.exceptions.ReadTimeoutError:
        if try_number >= retries:
          raise
        if not quiet:
          print("Docker push failed, retrying...")

  def pull(self, repository, tag="latest"):
    self.client.images.pull(repository=repository, tag=tag)

  def login(self, docker_login_credentials):
    creds = docker_login_credentials
    response = self.client.login(
      username=creds.username,
      password=creds.password,
      registry=creds.registry,
      dockercfg_path="/dev/null",
    )
    response_status = response.get("Status")
    if response_status:
      assert response_status == "Login Succeeded", (
        f"Docker failed logging into registry {creds.registry} with username {creds.username}",
      )

  @staticmethod
  def format_image_name(repository, tag):
    return f"{repository}:{tag}" if tag is not None else repository

  @staticmethod
  def get_repository_and_tag(image):
    image_regex = r"^([a-z0-9\_\-]+(?::[0-9]+)?\/?[a-z0-9\_\-]+)(:[a-zA-Z0-9\_\-\.]+)?$"
    match = re.match(image_regex, image)
    assert match, "image must match the regex: /" + image_regex + "/"
    groups = match.groups()
    repository = groups[0]
    tag = groups[1][1:] if groups[1] else None
    return repository, tag

  def get_image(self, tag):
    return self.client.images.get(tag)

  def remove_tag(self, tag):
    self.client.images.remove(tag)

  def untag(self, image):
    for tag in image.tags:
      self.client.images.remove(tag)

  def untag_all(self, label):
    for image in self.client.images.list(filters={"label": label}):
      self.untag(image)

  def image_exists_in_registry(self, repo, tag):
    try:
      for _ in self.client.api.pull(repo + ":" + tag, stream=True):
        return True
    except docker.errors.NotFound:
      pass
    return False

  def prune(self):
    self.client.images.prune(filters=dict(dangling=False))
