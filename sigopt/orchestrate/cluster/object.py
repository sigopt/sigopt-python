import base64

from ..docker.service import DockerLoginCredentials
from ..provider.constants import Provider, provider_to_string


class Cluster(object):
  def __init__(self, services, name, registry):
    self.services = services
    self._name = name
    self._registry = registry
    self._provider_service = None

  @property
  def name(self):
    return self._name

  @property
  def provider(self):
    raise NotImplementedError()

  @property
  def provider_string(self):
    return provider_to_string(self.provider)

  @property
  def provider_service(self):
    if self._provider_service is None:
      self._provider_service = self.services.provider_broker.get_provider_service(self.provider)
    return self._provider_service

  @property
  def registry(self):
    return self._registry

  def get_registry_login_credentials(self, repository):
    raise NotImplementedError()

  def generate_image_tag(self, repository):
    raise NotImplementedError()

class AWSCluster(Cluster):
  @property
  def provider(self):
    return Provider.AWS

  def get_registry_login_credentials(self, repository):
    ecr_service = self.provider_service.aws_services.ecr_service
    registry_id = ecr_service.ensure_repositories([repository])['repositories'][0]['registryId']
    authorization_data = ecr_service.get_authorization_token([registry_id])['authorizationData'][0]
    authorization_token = authorization_data['authorizationToken']
    decoded_bytes = base64.b64decode(authorization_token)
    (username, password) = decoded_bytes.decode('utf-8').split(':')
    proxy_endpoint = authorization_data['proxyEndpoint']
    return DockerLoginCredentials(
      registry=proxy_endpoint,
      username=username,
      password=password,
    )

  def generate_image_tag(self, repository):
    if self.registry is not None:
      return f"{self.registry}/{repository}"

    ecr_service = self.provider_service.aws_services.ecr_service
    descriptions = ecr_service.ensure_repositories([repository])
    return descriptions['repositories'][0]['repositoryUri']

class CustomCluster(Cluster):
  @property
  def provider(self):
    return Provider.CUSTOM

  def get_registry_login_credentials(self, repository):
    return None

  def generate_image_tag(self, repository):
    if self.registry is not None:
      return f"{self.registry}/{repository}"
    return repository
