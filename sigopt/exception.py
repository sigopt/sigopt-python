# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
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
    return "{0}: {1}".format(
      "ConnectionException",
      self.message if self.message is not None else "",
    )


class ApiException(SigOptException):
  """
    An exception that occurs when the SigOpt API was contacted successfully, but
    it responded with an error.
    """

  def __init__(self, body, status_code):
    self.message = body.get("message", None) if body is not None else None
    self._body = body
    if self.message is not None:
      super().__init__(self.message)
    else:
      super().__init__()
    self.status_code = status_code

  def __str__(self):
    return "{0} ({1}): {2}".format(
      "ApiException",
      self.status_code,
      self.message if self.message is not None else "",
    )

  def to_json(self):
    return copy.deepcopy(self._body)


class RunException(SigOptException):
  pass


class ConflictingProjectException(SigOptException):
  def __init__(self, project_id):
    super().__init__(f"The project with id '{project_id}' already exists.")


class ProjectNotFoundException(SigOptException):
  def __init__(self, project_id):
    super().__init__(
      f"The project '{project_id}' does not exist.\nTry any of the following"
      f" steps to resolve this:\n  * create a project with the ID '{project_id}'"
      f" with the command\n    `sigopt create project --project '{project_id}'`"
      " or by visiting\n    https://app.sigopt.com/projects\n  * change the"
      " project ID by setting the SIGOPT_PROJECT environment variable or\n    by"
      " renaming the current directory\n  * (advanced) if the project you want"
      " to use is in a different team,\n    change your API token by switching"
      " to that team and then going to\n    https://app.sigopt.com/tokens/info"
    )
