import argparse

import sigopt

# Take a suggestion from sigopt and evaluate your function
def execute_model(run):
  # train a model
  # evaluate a model
  # return the accuracy 
  raise NotImplementedError("Return a number, which represents your metric for this run")

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--budget', type=int, default=20)
  parser.add_argument('--client_token', required=True, help="Find your CLIENT_TOKEN at https://sigopt.com/tokens")
  the_args = parser.parse_args()

  # Descriptor of what kind of dataset you are modeling
  sigopt.log_dataset("Example dataset") 
  # Useful for keeping track of where you got the data
  sigopt.log_metadata(key="Dataset Source", value="Example Source")  
  # e.g. Sklern, xgboost, etc.
  sigopt.log_metadata(key="Feature Pipeline Name", value="Example Pipeline") 
  # What kind of learning you are attemping
  sigopt.log_model("Example Model Technique") 
  # Create an experiment with one paramter, x
  experiment = sigopt.create_experiment(
    name="Basic Test experiment",
    project="sigopt-examples",
    parameters=[{'name': 'x', 'bounds': {'max': 50.0, 'min': 0.0}, 'type': 'double'}],
    metrics=[{"name":"holdout_accuracy", "objective":"maximize"}],
    parallel_bandwidth=1,
    budget=the_args.budget,
  )
  print('Created experiment id {0}'.format(experiment.id))

  # In a loop: receive a suggestion, evaluate the metric, report an observation
  for run in experiment.loop():
    with run:
      holdout_accuracy = execute_model(run)
      run.log_metric("holdout_accuracy", holdout_accuracy)

    
  best_runs = experiment.get_best_runs()
