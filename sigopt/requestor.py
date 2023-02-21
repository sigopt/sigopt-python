# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import backoff
import os
import requests
from http import HTTPStatus

from .compat import json as simplejson
from .config import config
from .exception import ApiException, ConnectionException
from .objects import ApiObject
from .ratelimit import failed_status_rate_limit
from .version import VERSION

DEFAULT_API_URL = 'https://api.sigopt.com'
DEFAULT_HTTP_TIMEOUT = 150

class Requestor(object):
  def __init__(
    self,
    user,
    password,
    headers,
    verify_ssl_certs=None,
    proxies=None,
    timeout=DEFAULT_HTTP_TIMEOUT,
    client_ssl_certs=None,
    session=None,
  ):
    self._set_auth(user, password)
    self.default_headers = headers or {}
    self.verify_ssl_certs = verify_ssl_certs
    self.proxies = proxies
    self.timeout = timeout
    self.client_ssl_certs = client_ssl_certs
    self.session = session
    self.api_url = os.environ.get("SIGOPT_API_URL") or DEFAULT_API_URL

  def _set_auth(self, username, password):
    if username is not None:
      self.auth = requests.auth.HTTPBasicAuth(username, password)
    else:
      self.auth = None

  def _request_params(self, params):
    req_params = params or {}

    def serialize(value):
      if isinstance(value, (dict, list)):
        return simplejson.dumps(value)
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

  def _request(self, method, url, params, json, headers, user_agent):
    headers = self._with_default_headers(headers, user_agent)
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

  def request(self, method, path, data=None, headers=None, user_agent=None):
    url = "/".join([self.api_url, "v1"] + path)
    if method.upper() in ('GET', 'DELETE'):
      json, params = None, self._request_params(data)
    else:
      json, params = ApiObject.as_json(data), None
    retry = backoff.on_predicate(
      backoff.expo,
      lambda response: response.status_code == HTTPStatus.TOO_MANY_REQUESTS,
      max_time=self.timeout,
      jitter=backoff.full_jitter,
    )
    response = retry(self._request)(method, url, params, json, headers, user_agent)
    return self._handle_response(response)

  def _with_default_headers(self, headers, user_agent):
    user_agent_str = user_agent or 'sigopt-python/{0}'.format(VERSION)
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
