from __future__ import print_function

import argparse
import math
import threading
import time

from sigopt import Connection
import sigopt.examples


class ExampleRunner(threading.Thread):
  def __init__(self, client_token, experiment_id):
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
    This fictitious example has only two parameters, named x1 and x2
    """
    sleep_seconds = 10
    print('{0} - Sleeping for {1} seconds to simulate expensive computation...'.format(threading.current_thread(), sleep_seconds))
    time.sleep(sleep_seconds)
    return sigopt.examples.franke_function(assignments['x1'], assignments['x2'])

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--runner_count', type=int, default=2)
  parser.add_argument('--client_token', required=True, help="Find your CLIENT_TOKEN at https://sigopt.com/tokens")
  the_args = parser.parse_args()

  client_token = the_args.client_token
  conn = Connection(client_token=client_token)
  experiment = conn.experiments().create(
    name="Parallel Test Franke Function",
    parameters=[
      {'name': 'x1', 'bounds': {'max': 1.0, 'min': 0.0}, 'type': 'double'},
      {'name': 'x2', 'bounds': {'max': 1.0, 'min': 0.0}, 'type': 'double'},
    ],
  )

  runners = [ExampleRunner(client_token, experiment.id) for _ in range(the_args.runner_count)]

  for runner in runners:
    runner.daemon = True
    runner.start()

  for runner in runners:
    runner.join()
