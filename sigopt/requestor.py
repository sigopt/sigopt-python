import requests

from requests.auth import HTTPBasicAuth

class Requestor(object):
  def __init__(self, user=None, password=None, headers=None):
    self.auth = HTTPBasicAuth(user, password)
    self.default_headers = headers or {}

  def get(self, url, params=None, json=None, headers=None):
    headers = self._with_default_headers(headers)
    return requests.get(url, params=params, json=json, auth=self.auth, headers=headers)

  def post(self, url, params=None, json=None, headers=None):
    headers = self._with_default_headers(headers)
    return requests.post(url, params=params, json=json, auth=self.auth, headers=headers)

  def put(self, url, params=None, json=None, headers=None):
    headers = self._with_default_headers(headers)
    return requests.put(url, params=params, json=json, auth=self.auth, headers=headers)

  def delete(self, url, params=None, json=None, headers=None):
    headers = self._with_default_headers(headers)
    return requests.delete(url, params=params, json=json, auth=self.auth, headers=headers)

  def _with_default_headers(self, headers):
    headers = (headers or {}).copy()
    headers.update(self.default_headers)
    return headers
