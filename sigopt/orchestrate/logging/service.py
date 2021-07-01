import logging

from ..services.base import Service


class LoggingService(Service):
  def __init__(self, services, logger_name='sigopt'):
    super().__init__(services)
    self._logger = logging.getLogger(logger_name)

  @property
  def logger(self):
    return self._logger

  def debug(self, *args, **kwargs):
    return self.logger.debug(*args, **kwargs)

  def info(self, *args, **kwargs):
    return self.logger.info(*args, **kwargs)

  def warning(self, *args, **kwargs):
    return self.logger.warning(*args, **kwargs)

  def error(self, *args, **kwargs):
    return self.logger.error(*args, **kwargs)
