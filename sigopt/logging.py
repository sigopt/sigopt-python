import sys
from logging import getLogger, INFO, StreamHandler

print_logger = getLogger("sigopt.print")
print_logger.setLevel(INFO)

def enable_print_logging():
  global print_logger
  print_logger.addHandler(StreamHandler(stream=sys.stdout))
