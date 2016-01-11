from __future__ import print_function

import argparse
import threading
import time
# insert your CLIENT_TOKEN into sigopt_creds.py
# otherwise you'll see "This endpoint requires an authenticated user" errors
from sigopt_creds import CLIENT_TOKEN

from sigopt.interface import Connection


class ExampleRunner(threading.Thread):
  def __init__(self, experiment_id):
    threading.Thread.__init__(self)
    self.connection = Connection(client_token=CLIENT_TOKEN)
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
    return assignments['param1'] - assignments['param2']

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--runner_count', type=int, default=2)
  parser.add_argument('--experiment_id', type=int)
  the_args = parser.parse_args()

  if the_args.experiment_id is None:
    raise Exception("Must provide an experiment id. This experiment should have two numerical params: param1 and param2")

  runners = [ExampleRunner(the_args.experiment_id) for _ in range(the_args.runner_count)]

  for runner in runners:
    runner.daemon = True
    runner.start()

  for runner in runners:
    runner.join()
