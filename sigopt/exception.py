import copy


class SigOptException(Exception):
  pass


class ConnectionException(SigOptException):
  """
  An exception that occurs when the SigOpt API was unavailable.
  """
  def __init__(self, message):
    super().__init__(message)
    self.message = message

  def __str__(self):
    return '{0}: {1}'.format(
      'ConnectionException',
      self.message if self.message is not None else '',
    )

class ApiException(SigOptException):
  """
  An exception that occurs when the SigOpt API was contacted successfully, but
  it responded with an error.
  """
  def __init__(self, body, status_code):
    self.message = body.get('message', None) if body is not None else None
    self._body = body
    if self.message is not None:
      super().__init__(self.message)
    else:
      super().__init__()
    self.status_code = status_code

  def __str__(self):
    return '{0} ({1}): {2}'.format(
      'ApiException',
      self.status_code,
      self.message if self.message is not None else '',
    )

  def to_json(self):
    return copy.deepcopy(self._body)

class RunException(SigOptException):
  pass

class ProjectNotFoundException(SigOptException):
  def __init__(self, project_id):
    super().__init__(
      f"The project {project_id} does not exist.\n"
      "Try any of the following steps to resolve this:\n"
      f"  * create a project with the id '{project_id}' by visiting\n"
      "    https://app.sigopt.com/projects\n"
      "  * change the project id by setting the SIGOPT_PROJECT environment variable or\n"
      "    by renaming the current directory\n"
      f"  * (advanced) change to a team that has the project '{project_id}' then find your\n"
      "    API token for that team at https://app.sigopt.com/tokens/info"
    )
