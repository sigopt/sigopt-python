import mock
import pytest

from sigopt.request_driver import RequestDriver
from sigopt.version import VERSION


class TestRequestDriver:
  api_token = "test_api_token"
  api_url = "https://test.api.sigopt.ninja"
  timeout = -1
  user_agent_info = ("test", "info")

  @pytest.fixture(autouse=True)
  def patch_config(self):
    with mock.patch("sigopt.config.get_user_agent_info") as get_user_agent_info:
      get_user_agent_info.side_effect = [self.user_agent_info]
      yield

  @pytest.fixture
  def mock_session(self):
    return mock.Mock()

  @pytest.fixture
  def driver(self, mock_session):
    return RequestDriver(
      self.api_token,
      api_url=self.api_url,
      session=mock_session,
      timeout=self.timeout,
    )

  @pytest.mark.parametrize(
    "method,expected_method,uses_params",
    [
      ("get", "GET", True),
      ("Get", "GET", True),
      ("GET", "GET", True),
      ("DELETE", "DELETE", True),
      ("PUT", "PUT", False),
      ("POST", "POST", False),
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
      ({}, {}, {}),
      ({"id": 1}, {"id": "1"}, {"id": 1}),
      ({"id": "1"}, {"id": "1"}, {"id": "1"}),
      (
        {"assignments": {"x": 1, "y": 2}},
        {"assignments": '{"x":1,"y":2}'},
        {"assignments": {"x": 1, "y": 2}},
      ),
      (
        {"datasets": {"mnist": {}}, "source_code": {"hash": "xyz123"}},
        {"datasets": '{"mnist":{}}', "source_code": '{"hash":"xyz123"}'},
        {"datasets": {"mnist": {}}, "source_code": {"hash": "xyz123"}},
      ),
      (
        {"after": "", "before": "1234", "limit": 100},
        {"after": "", "before": "1234", "limit": "100"},
        {"after": "", "before": "1234", "limit": 100},
      ),
    ],
  )
  @pytest.mark.parametrize(
    "headers,expected_headers",
    [
      (None, {}),
      ({}, {}),
      ({"X-Response-Content": "skip"}, {"X-Response-Content": "skip"}),
    ],
  )
  @pytest.mark.parametrize(
    "response_code,response_data,returned_data",
    [
      (200, "{}", {}),
      (204, "", None),
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
    response_code,
    response_data,
    returned_data,
    expected_method,
    expected_url,
    expected_params,
    expected_json,
    expected_headers,
  ):
    mock_session.request = mock.Mock(
      side_effect=[
        mock.Mock(
          status_code=response_code,
          text=response_data,
        )
      ]
    )
    response = driver.request(method, path, data, headers)
    assert response == returned_data
    if uses_params:
      expected_json = None
    else:
      expected_params = None
    expected_headers.update(driver.default_headers)
    user_agent_info = "; ".join(self.user_agent_info)
    expected_headers.update(
      {
        "User-Agent": f"sigopt-python/{VERSION} ({user_agent_info})",
      }
    )
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
