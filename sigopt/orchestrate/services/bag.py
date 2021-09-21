class ServiceBag(object):
  """
  A top-level container for all of our services. A service bag should be passed
  around where needed to grant access to these services. This gives us
  dependency injection, and lets us reuse services when they have a startup
  cost (such as creating DB connections).
  """
  def __init__(self):
    self._create_services()
    self._warmup_services()

  def _create_services(self):
    pass

  def _warmup_services(self):
    pass
