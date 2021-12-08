DEFAULT_EVALS_NAME = 'TestSet'
DEFAULT_TRAINING_NAME = 'TrainingSet'
USER_SOURCE_NAME = 'User Specified'
XGBOOST_DEFAULTS_SOURCE_NAME = 'XGBoost Defaults'

# defaults
DEFAULT_BO_ITERATIONS = 50
DEFAULT_CLASSIFICATION_METRIC = 'accuracy'
DEFAULT_NUM_BOOST_ROUND = 10
DEFAULT_REGRESSION_METRIC = 'mean squared error'
DEFAULT_SEARCH_PARAMS = ['eta', 'gamma', 'max_depth', 'min_child_weight', 'num_boost_round']

# optimization metrics
CLASSIFICATION_METRIC_CHOICES = ['accuracy', 'F1', 'precision', 'recall']
REGRESSION_METRIC_CHOICES = ['mean absolute error', 'mean squared error']
SUPPORTED_METRICS_TO_OPTIMIZE = CLASSIFICATION_METRIC_CHOICES + REGRESSION_METRIC_CHOICES
METRICS_OPTIMIZATION_STRATEGY = {
  **dict(zip(CLASSIFICATION_METRIC_CHOICES, ['maximize']*len(CLASSIFICATION_METRIC_CHOICES))),
  **dict(zip(REGRESSION_METRIC_CHOICES, ['minimize']*len(REGRESSION_METRIC_CHOICES))),
}

# Note: only the XGB general params. Omitted monotone_constraints and interaction_constraints b/c more complex.
# Also omitting refresh_leaf b/c it's a boolean value. Only some of these have bounds which will be autofilled.
# We can add arbitrary bounds to the rest (and maybe we should).
PARAMETER_INFORMATION = {

  # Numerical Values
  'eta':                {'type': 'double', 'limits': '(0, Inf]', 'bounds': {'min': 0.001, 'max':   1},
                         'transformation': 'log'},
  'max_delta_step':     {'type': 'double', 'limits': '[0, Inf]', 'bounds': {'min': 0.001, 'max':  10},
                         'transformation': 'log'},
  'alpha':              {'type': 'double', 'limits': '[0, Inf]', 'bounds': {'min': 0,     'max':  10}},
  'gamma':              {'type': 'double', 'limits': '[0, Inf]', 'bounds': {'min': 0,     'max':   5}},
  'lambda':             {'type': 'double', 'limits': '[0, Inf]', 'bounds': {'min': 0,     'max':  10}},
  'max_depth':          {'type': 'int',    'limits': '[1, Inf]', 'bounds': {'min': 2,     'max':  16}},
  'min_child_weight':   {'type': 'double', 'limits': '[0, Inf]', 'bounds': {'min': 0,     'max':  10}},
  'num_boost_round':    {'type': 'int',    'limits': '[1, Inf]', 'bounds': {'min': 10,    'max': 200}},
  'colsample_bylevel':  {'type': 'double', 'limits': '(0,   1]', 'bounds': {'min': 0.5,   'max':   1}},
  'colsample_bynode':   {'type': 'double', 'limits': '(0,   1]', 'bounds': {'min': 0.5,   'max':   1}},
  'colsample_bytree':   {'type': 'double', 'limits': '(0,   1]', 'bounds': {'min': 0.5,   'max':   1}},
  'max_bin':            {'type': 'int',    'limits': '[1, Inf]'},
  'max_leaves':         {'type': 'int',    'limits': '[1, Inf]'},
  'num_parallel_tree':  {'type': 'int',    'limits': '[1, Inf]'},
  'scale_pos_weight':   {'type': 'double', 'limits': '[0, Inf]'},
  'sketch_eps':         {'type': 'double', 'limits': '(0,   1)'},
  'subsample':          {'type': 'double', 'limits': '(0,   1]', 'bounds': {'min': 0.5,   'max':   1}},

  # String values
  'grow_policy':        {'type': 'categorical', 'values': ['depthwise', 'lossguide']},
  'predictor':          {'type': 'categorical', 'values': ['auto', 'cpu_predictor', 'gpu_predictor']},
  'process_type':       {'type': 'categorical', 'values': ['default', 'update']},
  'sampling_method':    {'type': 'categorical', 'values': ['uniform', 'gradient_based']},
  'tree_method':        {'type': 'categorical', 'values': ['auto', 'exact', 'approx', 'hist', 'gpu_hist']},
  'updater':            {'type': 'categorical', 'values': ['grow_colmaker', 'grow_histmaker', 'grow_local_histmaker',
                                                           'grow_quantile_histmaker', 'grow_gpu_hist', 'sync',
                                                           'refresh', 'prune']},
}

SUPPORTED_AUTOBOUND_PARAMS = [
  name for name, info in PARAMETER_INFORMATION.items() if 'bounds' in info
]
