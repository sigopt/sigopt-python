import os

import pytest
from mock import Mock, patch

from sigopt.orchestrate.sigopt.service import SigOptService


class TestSigOptService(object):
  @pytest.fixture
  def services(self):
    return Mock()

  def test_with_api_token(self, services):
    sigopt_service = SigOptService(services, api_token='foobar')
    assert sigopt_service.conn is not None
    assert sigopt_service.api_token == 'foobar'

  def test_with_api_url(self, services):
    sigopt_service = SigOptService(services, api_url='https://api-env.sigopt.com')
    assert sigopt_service.conn is not None
    assert sigopt_service.api_url == 'https://api-env.sigopt.com'

  def test_reads_from_environment(self, services):
    with patch.dict(os.environ, dict(SIGOPT_API_TOKEN='foobar', SIGOPT_API_URL='https://api-env.sigopt.com')):
      sigopt_service = SigOptService(services)
      assert sigopt_service.conn is not None
      assert sigopt_service.api_token == 'foobar'
      assert sigopt_service.api_url == 'https://api-env.sigopt.com'

  def test_no_token_error(self, services):
    with patch.dict(os.environ, dict(SIGOPT_API_TOKEN='')):
      with pytest.raises(ValueError):
        SigOptService(services).check_connection()
