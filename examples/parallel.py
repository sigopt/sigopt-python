import argparse

import sigopt

def run_command_on_machine(machine_number, command):
  # log into machine
  # execute command
  raise NotImplementedError("Log into the specified machines, execute the included command")


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--budget', type=int, default=20)
  parser.add_argument('--parallel_bandwidth', type=int, default=3, help="Number of machines you are running learning on")
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
  experiment = sigopt.create_aiexperiment(
    name="Basic Test experiment",
    type="offline",
    parameters=[{'name': 'x', 'bounds': {'max': 50.0, 'min': 0.0}, 'type': 'double'}],
    metrics=[{"name":"holdout_accuracy", "objective":"maximize"}],
    parallel_bandwidth=the_args.parallel_bandwidth,
    budget=the_args.budget,
  )
  print('Created experiment id {0}'.format(experiment.id))

  # In a loop: on each machine, start off a learning process, then each reports separately
  # to Sigopt the results
  for machine_number in range(experiment.parallel_bandwidth):
    run_command_on_machine(
      machine_number,
      f"sigopt start-worker {experiment.id} python run-model.py",
    )


  best_runs = experiment.get_best_runs()
  print(best_runs)
