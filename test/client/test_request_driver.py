import mock
import pytest

from sigopt.request_driver import RequestDriver
from sigopt.version import VERSION


class TestRequestDriver:
  api_url = "https://test.api.sigopt.ninja"
  timeout = -1

  @pytest.fixture
  def mock_session(self):
    return mock.Mock()

  @pytest.fixture
  def driver(self, mock_session):
    return RequestDriver(api_url=self.api_url, session=mock_session, timeout=self.timeout)

  @pytest.mark.parametrize(
    "method,expected_method,uses_params",
    [
      ("get", "GET", True),
      ("Get", "GET", True),
      ("GET", "GET", True),
      ("PUT", "PUT", False),
      ("POST", "POST", False),
      ("DELETE", "DELETE", True),
      ("MERGE", "MERGE", False),
    ],
  )
  @pytest.mark.parametrize(
    "path,expected_url",
    [
      (["experiments"], "/v1/experiments"),
      (["experiments", 1], "/v1/experiments/1"),
      (["experiments", "1"], "/v1/experiments/1"),
      (["experiments", "1", "suggestions", "2"], "/v1/experiments/1/suggestions/2"),
    ],
  )
  @pytest.mark.parametrize(
    "data,expected_params,expected_json",
    [
      (None, {}, None),
    ],
  )
  @pytest.mark.parametrize(
    "headers,expected_headers",
    [
      (None, {}),
      ({}, {}),
    ],
  )
  def test_request(
    self,
    driver,
    mock_session,
    method,
    path,
    data,
    headers,
    uses_params,
    expected_method,
    expected_url,
    expected_params,
    expected_json,
    expected_headers,
  ):
    mock_session.request = mock.Mock(side_effect=[mock.Mock(
      status_code=200,
      text='{}',
    )])
    response = driver.request(method, path, data, headers)
    assert response == {}
    if uses_params:
      expected_json = None
    else:
      expected_params = None
    expected_headers.update(driver.default_headers)
    expected_headers.update({
      "User-Agent": f"sigopt-python/{VERSION}",
    })
    mock_session.request.assert_called_once_with(
      method=expected_method,
      url=f"{self.api_url}{expected_url}",
      params=expected_params,
      json=expected_json,
      auth=driver.auth,
      headers=expected_headers,
      verify=None,
      proxies=None,
      timeout=self.timeout,
      cert=None,
    )
