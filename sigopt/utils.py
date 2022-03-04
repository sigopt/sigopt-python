import contextlib
from http import HTTPStatus

from sigopt.exception import ApiException

class HandledException:
  def __init__(self):
    self.exception = None

@contextlib.contextmanager
def accept_sigopt_not_found():
  handled = HandledException()
  try:
    yield handled
  except ApiException as ae:
    if ae.status_code != HTTPStatus.NOT_FOUND:
      raise
    handled.exception = ae

# Refer: https://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-input
def query_yes_no(question, default="yes"):
  """Ask a yes/no question via raw_input() and return their answer.

  "question" is a string that is presented to the user.
  "default" is the presumed answer if the user just hits <Enter>.
      It must be "yes" (the default), "no" or None (meaning
      an answer is required of the user).

  The "answer" return value is True for "yes" or False for "no".
  """
  valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
  if default is None:
    prompt = " [y/n] "
  elif default == "yes":
    prompt = " [Y/n] "
  elif default == "no":
    prompt = " [y/N] "
  else:
    raise ValueError("invalid default answer: '%s'" % default)

  while True:
    print(question + prompt)
    choice = input().lower()
    if default is not None and choice == "":
      return valid[default]
    elif choice in valid:
      return valid[choice]
    else:
      print("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")
