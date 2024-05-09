# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from ..decorators import public
from .compat import xgboost


class SigOptCheckpointCallback(xgboost.callback.TrainingCallback):
  def __init__(self, run, period=1):
    self.run = run
    self.period = period
    self._latest = None
    super().__init__()

  @public
  def after_iteration(self, model, epoch, evals_log):
    if not evals_log:
      return False

    checkpoint_logs = {}
    for dataset, metric_dict in evals_log.items():
      for metric_label, metric_record in metric_dict.items():
        if isinstance(metric_record[-1], tuple):
          chkpt_value = metric_record[-1][0]
        else:
          chkpt_value = metric_record[-1]
        checkpoint_logs.update({"-".join((dataset, metric_label)): chkpt_value})
    if (epoch % self.period) == 0 or self.period == 1:
      self.run.log_checkpoint(checkpoint_logs)
      self._latest = None
    else:
      self._latest = checkpoint_logs

    return False

  @public
  def after_training(self, model):
    if self._latest is not None:
      self.run.log_checkpoint(self._latest)
    return model
