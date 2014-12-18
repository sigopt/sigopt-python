class ReportResponse(object):
  def __init__(self, api_response):
    self.api_response = api_response

  def get_parameters(self):
    return self.api_response['suggestion']['allocations']

class SuggestResponse(object):
  def __init__(self, api_response):
    self.api_response = api_response

  def get_parameters(self):
    return self.api_response['suggestion']['allocations']
