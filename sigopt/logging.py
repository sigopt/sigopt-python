import sys
import traceback
from logging import getLogger, INFO, StreamHandler

print_logger = getLogger("sigopt.print")
print_logger.setLevel(INFO)
print_logger.info = lambda *args, **kwargs: traceback.print_stack()

stdout_handler = StreamHandler(stream=sys.stdout)

def enable_print_logging():
  global print_logger, stdout_handler
  print_logger.removeHandler(stdout_handler)
  print_logger.addHandler(stdout_handler)
