import threading
import time

from sigopt.interface import Connection

# Just fill these in with your credentials
CLIENT_TOKEN = 'XXXXXXXXXX'
USER_TOKEN = 'YYYYYYYYY'
CLIENT_ID = 0
EXPERIMENT_ID = 0

class ExampleRunner(threading.Thread):
  def __init__(self, worker_id):
    threading.Thread.__init__(self)
    self.worker_id = worker_id
    self.connection = Connection(client_token=CLIENT_TOKEN, worker_id=self.worker_id)

  def run(self):
    while True:
      assignments = self.connection.experiment_suggest(EXPERIMENT_ID).suggestion.assignments
      print '{0} - Evaluating at parameters: {1}'.format(self.worker_id, assignments)
      metric_value = self.evaluate(assignments)
      print '{0} - Observed value: {1}'.format(self.worker_id, metric_value)
      self.connection.experiment_report(EXPERIMENT_ID, {
        'assignments': assignments,
        'value': metric_value,
      })

  def evaluate(self, assignments):
    """
    Replace this with the function you want to optimize
    This fictitious example has only two parameters, named param1 and param2
    """
    sleep_seconds = 10
    print '{0} - Sleeping for {1} seconds to simulate expensive computation...'.format(self.worker_id, sleep_seconds)
    time.sleep(sleep_seconds)
    return assignments['param1'] - assignments['param2']

if __name__ == '__main__':

  RUNNER_COUNT = 2
  runners = [ExampleRunner('worker-' + str(i+1)) for i in xrange(RUNNER_COUNT)]

  for runner in runners:
    runner.daemon = True
    runner.start()

  while True:
    time.sleep(1)
    if all((not r.is_alive() for r in runners)):
      break
