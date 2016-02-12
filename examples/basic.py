import argparse

# insert your client_token into sigopt_creds.py
# otherwise you'll see "This endpoint requires an authenticated user" errors
from sigopt_creds import client_token

from sigopt.interface import Connection

# Take a suggestion from sigopt and evaluate your function
def evaluate_metric(assignments):
  x = assignments['x']
  raise NotImplementedError("Return a number, which represents your metric evaluated at x")

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--iterations', type=int, default=20)
  the_args = parser.parse_args()

  connection = Connection(client_token=client_token)

  # Create an experiment with one paramter, x
  experiment = connection.experiments().create(
    name="Basic Test experiment",
    parameters=[{'name': 'x', 'bounds': {'max': 50.0, 'min': 0.0}, 'type': 'double'}],
  )
  print('Created experiment id {0}'.format(experiment.id))

  # In a loop: receive a suggestion, evaluate the metric, report an observation
  for _ in range(the_args.iterations):
    suggestion = connection.experiments(experiment.id).suggestions().create()
    print('Evaluating at suggested assignments: {0}'.format(suggestion.assignments))
    value = evaluate_metric(suggestion.assignments)
    print('Reporting observation of value: {0}'.format(value))
    connection.experiments(experiment.id).observations().create(
      suggestion=suggestion.id,
      value=value,
    )
