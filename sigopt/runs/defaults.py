import datetime
import re
import os

from ..exception import ApiException
from ..vendored import six

INVALID_PROJECT_ID_STRING_CHARACTERS = re.compile(r'[^a-z0-9\-_\.]')

def normalize_project_id(project_id):
  project_id = project_id.lower()
  return re.sub(INVALID_PROJECT_ID_STRING_CHARACTERS, '', project_id)

def get_default_project():
  project_id = os.environ.get('SIGOPT_PROJECT')
  if not project_id:
    project_id = os.path.basename(os.getcwd())
  return normalize_project_id(project_id)

def get_default_name(project):
  datetime_string = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  return six.u('{project} {datetime_string}').format(
    project=project,
    datetime_string=datetime_string,
  )

def ensure_project_exists(connection, client_id, project_id):
  try:
    connection.clients(client_id).projects().create(id=project_id, name=project_id)
  except ApiException as e:
    if e.status_code != 409:
      raise
