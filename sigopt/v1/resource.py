from ..resource import BaseApiResource
from ..endpoint import ApiEndpoint

class ApiResource(BaseApiResource):
  def __init__(self, conn, name, endpoints=None, resources=None):
    super(ApiResource, self).__init__(
      conn=conn,
      name=name,
      version='v1',
      endpoints=endpoints,
      resources=resources,
    )
