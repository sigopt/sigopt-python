# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import backoff
import os
import requests
from http import HTTPStatus
from requests.adapters import HTTPAdapter

from .compat import json as simplejson
from .config import config
from .exception import ApiException, ConnectionException
from .objects import ApiObject
from .ratelimit import failed_status_rate_limit
from .urllib3_patch import ExpiringHTTPConnectionPool, ExpiringHTTPSConnectionPool
from .version import VERSION

DEFAULT_API_URL = 'https://api.sigopt.com'
DEFAULT_HTTP_TIMEOUT = 150


def get_expiring_session():
  adapter = HTTPAdapter()
  adapter.poolmanager.pool_classes_by_scheme = {
    "http": ExpiringHTTPConnectionPool,
    "https": ExpiringHTTPSConnectionPool,
  }
  session = requests.Session()
  session.mount("http://", adapter)
  session.mount("https://", adapter)
  return session

class RequestDriver(object):
  api_version = "v1"

  def __init__(
    self,
    client_token=None,
    headers=None,
    proxies=None,
    timeout=DEFAULT_HTTP_TIMEOUT,
    client_ssl_certs=None,
    session=None,
    api_url=None,
  ):
    if client_token is None:
      client_token = os.environ.get("SIGOPT_API_TOKEN", config.api_token)
    if not client_token:
      raise ValueError("Must provide client_token or set environment variable SIGOPT_API_TOKEN")
    self.auth = None
    self.set_client_token(client_token)
    # no-verify overrides a passed in path
    no_verify_ssl_certs = os.environ.get("SIGOPT_API_NO_VERIFY_SSL_CERTS")
    if no_verify_ssl_certs:
      self.verify_ssl_certs = False
    else:
      self.verify_ssl_certs = os.environ.get("SIGOPT_API_VERIFY_SSL_CERTS")
    self.proxies = proxies
    self.timeout = timeout
    self.client_ssl_certs = client_ssl_certs
    self.session = session or get_expiring_session()
    self.api_url = api_url or os.environ.get("SIGOPT_API_URL") or DEFAULT_API_URL
    self.default_headers = {
      'Content-Type': 'application/json',
      'X-SigOpt-Python-Version': VERSION,
    }
    if headers:
      self.default_headers.update(headers)

  def _set_auth(self, username, password):
    if username is not None:
      self.auth = requests.auth.HTTPBasicAuth(username, password)
    else:
      self.auth = None

  def _request_params(self, params):
    req_params = params or {}

    def serialize(value):
      if isinstance(value, (dict, list)):
        return simplejson.dumps(value, indent=None, separators=(",", ":"))
      return str(value)

    return dict((
      (key, serialize(ApiObject.as_json(value)))
      for key, value
      in req_params.items()
      if value is not None
    ))

  def set_client_token(self, client_token):
    self._set_auth(client_token, '')

  def set_api_url(self, api_url):
    self.api_url = api_url

  def _request(self, method, url, params, json, headers):
    headers = self._with_default_headers(headers)
    try:
      caller = (self.session or requests)
      response = caller.request(
        method=method,
        url=url,
        params=params,
        json=json,
        auth=self.auth,
        headers=headers,
        verify=self.verify_ssl_certs,
        proxies=self.proxies,
        timeout=self.timeout,
        cert=self.client_ssl_certs,
      )
    except requests.exceptions.RequestException as rqe:
      message = ['An error occurred connecting to SigOpt.']
      if not url or not url.startswith(DEFAULT_API_URL):
        message.append('The host may be misconfigured or unavailable.')
      message.append('Contact support@sigopt.com for assistance.')
      message.append('')
      message.append(str(rqe))
      raise ConnectionException('\n'.join(message)) from rqe
    return response

  def request(self, method, path, data, headers):
    method = method.upper()
    url = "/".join(str(v) for v in (self.api_url, self.api_version, *path))
    if method in ('GET', 'DELETE'):
      json, params = None, self._request_params(data)
    else:
      json, params = ApiObject.as_json(data), None
    retry = backoff.on_predicate(
      backoff.expo,
      lambda response: response.status_code == HTTPStatus.TOO_MANY_REQUESTS,
      max_time=self.timeout,
      jitter=backoff.full_jitter,
    )
    response = retry(self._request)(method, url, params, json, headers)
    return self._handle_response(response)

  def _with_default_headers(self, headers):
    user_agent_str = f'sigopt-python/{VERSION}'
    user_agent_info = config.get_user_agent_info()
    if user_agent_info:
      user_agent_info_str = ''.join([
        '(',
        '; '.join(user_agent_info),
        ')',
      ])
      user_agent_str = ' '.join([user_agent_str, user_agent_info_str])

    request_headers = {'User-Agent': user_agent_str}

    if headers:
      request_headers.update(headers)

    request_headers.update(self.default_headers)
    return request_headers

  def _handle_response(self, response):
    status_code = response.status_code
    is_success = 200 <= status_code <= 299

    if status_code == 204:
      response_json = None
    else:
      try:
        response_json = simplejson.loads(response.text)
      except ValueError:
        response_json = {'message': response.text}
        status_code = 500 if is_success else status_code

    if is_success:
      failed_status_rate_limit.clear()
      return response_json
    failed_status_rate_limit.increment_and_check()
    raise ApiException(response_json, status_code)
