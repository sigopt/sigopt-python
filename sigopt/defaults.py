import datetime
import http
import re
import os

from .exception import ApiException

INVALID_PROJECT_ID_STRING_CHARACTERS = re.compile(r'[^a-z0-9\-_\.]')
VALID_PROJECT_ID = re.compile(r'[a-z0-9\-_\.]+\Z')

def normalize_project_id(project_id):
  project_id = project_id.lower()
  return re.sub(INVALID_PROJECT_ID_STRING_CHARACTERS, '', project_id)

def check_valid_project_id(project_id):
  if not VALID_PROJECT_ID.match(project_id):
    raise ValueError(f"project id is invalid: {project_id}")

def get_default_project():
  project_id = os.environ.get('SIGOPT_PROJECT')
  if project_id:
    check_valid_project_id(project_id)
    return project_id
  cwd_project_id = os.path.basename(os.getcwd())
  project_id = normalize_project_id(cwd_project_id)
  try:
    check_valid_project_id(project_id)
  except ValueError as ve:
    raise ValueError(
      f"The current directory '{cwd_project_id}' could not be converted into a valid project id."

      " Please rename the directory or use the SIGOPT_PROJECT environment variable instead."
    ) from ve
  return project_id

def get_default_name(project):
  datetime_string = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  return f'{project} {datetime_string}'

def ensure_project_exists(connection, project_id):
  client_id = connection.tokens('self').fetch().client
  try:
    connection.clients(client_id).projects().create(id=project_id, name=project_id)
  except ApiException as e:
    if e.status_code != http.HTTPStatus.CONFLICT:
      raise
  return client_id
