import logging
import threading


class ControllerThread(threading.Thread):
  def __init__(self, target, stop_threads_event, args, kwargs):
    super().__init__(target=self.wrap_target, args=args, kwargs=kwargs)
    self.target = target
    self.exception_occurred = threading.Event()
    self.stop_threads_event = stop_threads_event
    self.logger = logging.getLogger(f"controller:{type(self).__name__}")

  def wrap_target(self, *args, **kwargs):
    try:
      self.target(*args, **kwargs)
    except Exception as e:
      self.logger.error("exception occurred in thread: %s", e)
      self.exception_occurred.set()
      raise
    finally:
      self.stop_threads_event.set()
