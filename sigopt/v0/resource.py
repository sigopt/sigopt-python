from ..resource import BaseApiResource
from ..endpoint import ApiEndpoint

class ApiResource(BaseApiResource):
  def __init__(self, conn, name, response_cls, endpoints):
    super(ApiResource, self).__init__(
      conn=conn,
      name=name,
      response_cls=response_cls,
      version='v0',
      endpoints=(endpoints + [
        ApiEndpoint(None, response_cls, 'GET', 'fetch'),
      ])
    )

  def create(self, **kwargs):
    return self._response_cls(
      self._conn._post(self._base_url('create'), kwargs),
    )

  def _base_url(self, suffix):
    return '{api_url}/{version}/{name}/{suffix}'.format(
      api_url=self._conn.api_url,
      version=self._version,
      name=self._name,
      suffix=suffix,
    )
