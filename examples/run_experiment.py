import threading
import time

from sigopt.interface import Connection

# Just fill these in with your credentials
CLIENT_TOKEN = 'XXXXXXXXXX'
EXPERIMENT_ID = 0

class ExampleRunner(threading.Thread):
  def __init__(self, worker_id):
    threading.Thread.__init__(self)
    self.worker_id = worker_id
    self.connection = Connection(CLIENT_TOKEN, EXPERIMENT_ID, self.worker_id)

  def run(self):
    parameters = self.connection.suggest().get_parameters()
    while True:
      print '{0} - Evaluating at parameters: {1}'.format(self.worker_id, parameters)
      metric_value = self.evaluate(parameters)
      print '{0} - Observed value: {1}'.format(self.worker_id, metric_value)
      response = self.connection.report({
        'points': parameters,
        'value': metric_value,
      })
      parameters = response.get_parameters()

  def evaluate(self, parameters):
    # Substitute this for your metric function
    # This fictitious example has only two parameters, named param1 and param2
    sleep_seconds = 60
    print '{0} - Sleeping for {1} seconds to simulate expensive computation...'.format(self.worker_id, sleep_seconds)
    time.sleep(sleep_seconds)
    return parameters['param1'] - parameters['param2']

if __name__ == '__main__':
  RUNNER_COUNT = 3
  runners = [ExampleRunner('worker-' + str(i+1)) for i in xrange(RUNNER_COUNT)]

  for runner in runners:
    runner.daemon = True
    runner.start()

  while True:
    time.sleep(1)
    if all((not r.is_alive() for r in runners)):
      break
