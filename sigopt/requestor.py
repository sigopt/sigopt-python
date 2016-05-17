import requests

from .exception import ApiException, ConnectionException

DEFAULT_API_URL = 'https://api.sigopt.com'

class Requestor(object):
  def __init__(self, user, password, headers):
    if user is not None:
      self.auth = requests.auth.HTTPBasicAuth(user, password)
    else:
      self.auth = None
    self.default_headers = headers or {}

  def get(self, url, params=None, json=None, headers=None):
    return self._request('get', url=url, params=params, json=json, headers=headers)

  def post(self, url, params=None, json=None, headers=None):
    return self._request('post', url=url, params=params, json=json, headers=headers)

  def put(self, url, params=None, json=None, headers=None):
    return self._request('put', url=url, params=params, json=json, headers=headers)

  def delete(self, url, params=None, json=None, headers=None):
    return self._request('delete', url=url, params=params, json=json, headers=headers)

  def _request(self, method, url, params=None, json=None, headers=None):
    headers = self._with_default_headers(headers)
    try:
      response = requests.request(
        method=method,
        url=url,
        params=params,
        json=json,
        auth=self.auth,
        headers=headers,
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
    try:
      response_json = response.json()
    except ValueError:
      raise ApiException({'message': response.text}, response.status_code)

    if 200 <= response.status_code <= 299:
      return response_json
    else:
      raise ApiException(response_json, response.status_code)
