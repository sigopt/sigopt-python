import click
from simple_model import train_model

def exp_config():
  parameters = [
    {
      'name': 'max_depth',
      'type': 'int',
      'bounds': {'min': 2, 'max': 5}
    },
    {
      'name': 'num_boost_round',
      'type': 'int',
      'bounds': {'min': 2, 'max': 5}
    },
  ]
  config = {
    'name': 'simple-experiment-test',
    'type': 'offline',
    'parameters': parameters,
    'metrics': [{
      'name': 'accuracy',
      'strategy': 'optimize',
      'objective': 'maximize'
    }],
    'parallel_bandwidth': 1,
    'budget': 3
  }
  return config

@click.command()
@click.argument('mode', default='run')
def main(mode):
  import sigopt.xgboost.simple
  run_options = None
  experiment_config = exp_config()

  sigopt.xgboost.simple.set_mode(mode, run_options, experiment_config)
  model = train_model()

  if mode == 'run':
    print(model.run)
    print(model.get_run())
  elif mode == 'experiment':
    print(model.experiment)
    print(model.get_experiment())

if __name__ == '__main__':
  main()
