class ProxyMethod(object):
  instance = None

  def __init__(self, method_name):
    self.method_name = method_name

  @property
  def _bound_method(self):
    return getattr(self.instance, self.method_name)

  def __getattribute__(self, name):
    if name == '__doc__':
      return self._bound_method.__doc__
    return super(ProxyMethod, self).__getattribute__(name)

  def __call__(self, *args, **kwargs):
    return self._bound_method(*args, **kwargs)
