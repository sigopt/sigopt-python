import argparse

from sigopt import Connection

# Take a suggestion from sigopt and evaluate your function
def evaluate_metric(assignments):
  x = assignments['x']
  raise NotImplementedError("Return a number, which represents your metric evaluated at x")

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--observation_budget', type=int, default=20)
  parser.add_argument('--client_token', required=True, help="Find your CLIENT_TOKEN at https://sigopt.com/tokens")
  the_args = parser.parse_args()

  connection = Connection(client_token=the_args.client_token, _show_deprecation_warning=False)

  # Create an experiment with one paramter, x
  experiment = connection.experiments().create(
    name="Basic Test experiment",
    project="sigopt-examples",
    parameters=[{'name': 'x', 'bounds': {'max': 50.0, 'min': 0.0}, 'type': 'double'}],
    observation_budget=the_args.observation_budget,
  )
  print('Created experiment id {0}'.format(experiment.id))

  # In a loop: receive a suggestion, evaluate the metric, report an observation
  for _ in range(experiment.observation_budget):
    suggestion = connection.experiments(experiment.id).suggestions().create()
    print('Evaluating at suggested assignments: {0}'.format(suggestion.assignments))
    value = evaluate_metric(suggestion.assignments)
    print('Reporting observation of value: {0}'.format(value))
    connection.experiments(experiment.id).observations().create(
      suggestion=suggestion.id,
      value=value,
    )
