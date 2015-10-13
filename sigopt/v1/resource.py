from sigopt_client.resource import BaseApiResource
from sigopt_client.endpoint import ApiEndpoint

class ApiResource(BaseApiResource):
  def __init__(self, conn, name, response_cls, endpoints=[], resources=[]):
    super(ApiResource, self).__init__(
      conn=conn,
      name=name,
      response_cls=response_cls,
      version='v1',
      endpoints=(endpoints + [
        ApiEndpoint(None, response_cls, 'POST', 'create'),
        ApiEndpoint(None, response_cls, 'GET', 'fetch'),
        ApiEndpoint(None, response_cls, 'PUT', 'update'),
        ApiEndpoint(None, response_cls, 'DELETE', 'delete'),
      ]),
      resources=resources,
    )
