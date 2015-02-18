from sigopt.objects import ApiObject, Experiment, Suggestion

class ApiResponse(ApiObject):
  pass


class ExperimentsSuggestResponse(ApiResponse):
  @property
  def suggestion(self):
    _suggestion = self.body.get('suggestion')
    return Suggestion(_suggestion) if _suggestion is not None else None


class ExperimentsCreateResponse(ApiResponse):
  @property
  def experiment(self):
    _experiment = self.body.get('experiment')
    return Experiment(_experiment) if _experiment is not None else None
