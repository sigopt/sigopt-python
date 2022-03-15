import click
from simple_model import train_predict_save

run_options = {}
parameters = [
  {
    'name': 'max_depth',
    'type': 'int',
    'bounds': {'min': 2, 'max': 5}
  },
]
experiment_config = {
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

@click.command()
@click.argument('mode', default='run')
def main(mode):
  import sigopt.xgboost.simple
  sigopt.xgboost.simple.set_mode(mode, run_options, experiment_config)
  model = train_predict_save()

  if mode == 'run':
    print(model.run)
    print(model.get_run())
  elif mode == 'experiment':
    print(model.experiment)
    print(model.get_experiment())

if __name__ == '__main__':
  main()
