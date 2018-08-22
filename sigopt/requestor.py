import requests

from .compat import json as simplejson
from .exception import ApiException, ConnectionException

DEFAULT_API_URL = 'https://api.sigopt.com'

class Requestor(object):
  def __init__(self, user, password, headers, verify_ssl_certs=True, proxies=None):
    if user is not None:
      self.auth = requests.auth.HTTPBasicAuth(user, password)
    else:
      self.auth = None
    self.default_headers = headers or {}
    self.verify_ssl_certs = verify_ssl_certs
    self.proxies = proxies
    self._session = requests.Session()

  def get(self, url, params=None, json=None, headers=None):
    return self.request('get', url=url, params=params, json=json, headers=headers)

  def post(self, url, params=None, json=None, headers=None):
    return self.request('post', url=url, params=params, json=json, headers=headers)

  def put(self, url, params=None, json=None, headers=None):
    return self.request('put', url=url, params=params, json=json, headers=headers)

  def delete(self, url, params=None, json=None, headers=None):
    return self.request('delete', url=url, params=params, json=json, headers=headers)

  def request(self, method, url, params=None, json=None, headers=None):
    headers = self._with_default_headers(headers)
    try:
      response = self._session.request(
        method=method,
        url=url,
        params=params,
        json=json,
        auth=self.auth,
        headers=headers,
        verify=self.verify_ssl_certs,
        proxies=self.proxies,
      )
    except requests.exceptions.RequestException as e:
      message = ['An error occurred connecting to SigOpt.']
      if not url or not url.startswith(DEFAULT_API_URL):
        message.append('The host may be misconfigured or unavailable.')
      message.append('Contact support@sigopt.com for assistance.')
      message.append('')
      message.append(str(e))
      raise ConnectionException('\n'.join(message))
    return self._handle_response(response)

  def _with_default_headers(self, headers):
    headers = (headers or {}).copy()
    headers.update(self.default_headers)
    return headers

  def _handle_response(self, response):
    status_code = response.status_code
    is_success = 200 <= status_code <= 299

    try:
      response_json = simplejson.loads(response.text)
    except ValueError:
      response_json = {'message': response.text}
      status_code = 500 if is_success else status_code

    if is_success:
      return response_json
    raise ApiException(response_json, status_code)
