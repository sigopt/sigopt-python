import click
from simple_model import train_model

@click.command()
@click.argument('mode', default='run')
def main(mode):
  import sigopt.xgboost.simple
  run_options = None
  experiment_config = None
  mode = 'run'
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
