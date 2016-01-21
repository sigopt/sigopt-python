from __future__ import print_function

import argparse
import math
import threading
import time
# insert your client_token into sigopt_creds.py
# otherwise you'll see "This endpoint requires an authenticated user" errors
from sigopt_creds import client_token

from sigopt.interface import Connection


class ExampleRunner(threading.Thread):
  def __init__(self, experiment_id):
    threading.Thread.__init__(self)
    self.connection = Connection(client_token=client_token)
    self.experiment_id = experiment_id

  def run(self):
    while True:
      suggestion = self.connection.experiments(self.experiment_id).suggestions().create()
      print('{0} - Evaluating at parameters: {1}'.format(threading.current_thread(), suggestion.assignments))
      value = self.evaluate_metric(suggestion.assignments)
      print('{0} - Observed value: {1}'.format(threading.current_thread(), value))
      self.connection.experiments(self.experiment_id).observations().create(
        suggestion=suggestion.id,
        value=value,
      )

  def evaluate_metric(self, assignments):
    """
    Replace this with the function you want to optimize
    This fictitious example has only two parameters, named param1 and param2
    """
    sleep_seconds = 10
    print('{0} - Sleeping for {1} seconds to simulate expensive computation...'.format(threading.current_thread(), sleep_seconds))
    time.sleep(sleep_seconds)
    x1 = assignments['x1']
    x2 = assignments['x2']
    # EggHolder function - http://www.sfu.ca/~ssurjano/egg.html
    return -(x2 + 47) * math.sin(math.sqrt(abs(x2 + x1 / 2 + 47))) - x1 * math.sin(math.sqrt(abs(x1 - (x2 + 47))))

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--runner_count', type=int, default=2)
  the_args = parser.parse_args()

  conn = Connection(client_token=client_token)
  experiment = conn.experiments().create(
    name="Parallel Test Eggholder Function",
    parameters=[
      {'name': 'x1', 'bounds': {'max': 100.0, 'min': -100.0}, 'type': 'double'},
      {'name': 'x2', 'bounds': {'max': 100.0, 'min': -100.0}, 'type': 'double'},
    ],
  )

  runners = [ExampleRunner(experiment.id) for _ in range(the_args.runner_count)]

  for runner in runners:
    runner.daemon = True
    runner.start()

  for runner in runners:
    runner.join()
