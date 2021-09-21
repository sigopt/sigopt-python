import ssl

from kubernetes.client.rest import RESTClientObject
from requests.adapters import HTTPAdapter


class KubeProxyHTTPAdapter(HTTPAdapter):
  def __init__(self, k8s_api_client, **kwargs):
    self.k8s_api_client = k8s_api_client
    super().__init__(**kwargs)

  def add_headers(self, request, **_):
    query = []
    self.k8s_api_client.update_params_for_auth(request.headers, query, auth_settings=["BearerToken"])
    assert not query, "query string based auth not yet supported"

  def init_poolmanager(self, connections, maxsize, block=None, **_):
    rest_client = RESTClientObject(self.k8s_api_client.configuration, pools_size=connections, maxsize=maxsize)
    self.poolmanager = rest_client.pool_manager

  def cert_verify(self, conn, url, verify, cert):
    # NOTE(taylor): Session.request tries to reset the certificate (why???) so just make sure certs are required and
    # carry on
    assert conn.cert_reqs == ssl.CERT_REQUIRED
