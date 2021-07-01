import pytest
from mock import Mock

from sigopt.orchestrate.docker.service import DockerService


class TestDockerService(object):
  @pytest.fixture()
  def docker_service(self):
    services = Mock()
    return DockerService(services, Mock())

  def test_get_repository_and_tag_bad(self, docker_service):
    bad_images = [
      'my.registry.com:port/username/repo:tag',
      'username//repo',
      'username/repo:tag1:tag2',
      '',
      'username/repo:tag/test',
      'USERNAME/REPO:tag',
      'username/repo:',
      'username/repo: ',
    ]
    for image in bad_images:
      with pytest.raises(AssertionError):
        docker_service.get_repository_and_tag(image)

  def test_get_repository_and_tag_good(self, docker_service):
    image = 'username/repo:tag'
    repository, tag = docker_service.get_repository_and_tag(image)
    assert repository == 'username/repo' and tag == 'tag'

    image = 'repo'
    repository, tag = docker_service.get_repository_and_tag(image)
    assert repository == 'repo' and tag is None

    image = 'username_1-2/repo_1-2:tag'
    repository, tag = docker_service.get_repository_and_tag(image)
    assert repository == 'username_1-2/repo_1-2' and tag == 'tag'

    image = 'username/repo:tag_1-2'
    repository, tag = docker_service.get_repository_and_tag(image)
    assert repository == 'username/repo' and tag == 'tag_1-2'

    image = 'username/repo:TAG'
    repository, tag = docker_service.get_repository_and_tag(image)
    assert repository == 'username/repo' and tag == 'TAG'

    image = 'username/repo:tag1.2'
    repository, tag = docker_service.get_repository_and_tag(image)
    assert repository == 'username/repo' and tag == 'tag1.2'
