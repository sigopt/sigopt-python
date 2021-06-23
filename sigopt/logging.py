import logging
import sys

print_logger = logging.getLogger("sigopt.print")
print_logger.setLevel(logging.INFO)

def enable_print_logging():
  global print_logger
  print_logger.addHandler(logging.StreamHandler(stream=sys.stdout))
