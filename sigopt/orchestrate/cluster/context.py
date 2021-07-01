from .errors import PleaseDisconnectError


class DisconnectOnException(object):
  def __init__(self, cluster_name, services):
    self._cluster_name = cluster_name
    self._services = services

  def __enter__(self):
    pass

  def __exit__(self, t, exc, tb):
    if exc is not None:
      try:
        self._services.cluster_service.disconnect(cluster_name=self._cluster_name, disconnect_all=False)
        return False
      except Exception as disconnect_exception:
        raise PleaseDisconnectError(self._cluster_name) from disconnect_exception
    return None
