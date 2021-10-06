from ..base import sigopt_cli


@sigopt_cli.group("training_run")
def training_run_command():
  '''Commands for managing SigOpt TrainingRuns.'''
