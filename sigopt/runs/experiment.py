from .context import LiveRunContext


class ExperimentContext(object):
  def __init__(self, connection, experiment):
    self._connection = connection
    self._experiment = experiment

  def create_run(self, name=None):
    return LiveRunContext.create(
      connection=self._connection,
      run_name=name,
      project_id=self._experiment.project,
    )
