import requests

from .exception import ApiException

class Requestor(object):
  def __init__(self, user=None, password=None, headers=None):
    self.auth = requests.auth.HTTPBasicAuth(user, password)
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
    return self._handle_response(requests.request(
      method=method,
      url=url,
      params=params,
      json=json,
      auth=self.auth,
      headers=headers,
    ))

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
