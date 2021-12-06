
DEFAULT_EVALS_NAME = 'TestSet'
DEFAULT_TRAINING_NAME = 'TrainingSet'
USER_SOURCE_NAME = 'User Specified'
XGBOOST_DEFAULTS_SOURCE_NAME = 'XGBoost Defaults'

# search space
SEARCH_BOUNDS = [
  {'name': 'alpha',             'type': 'double',                           'bounds': {'min': 0, 'max': 10}},
  {'name': 'eta',               'type': 'double', 'transformation': 'log',  'bounds': {'min': 0.001, 'max': 1}},
  {'name': 'gamma',             'type': 'double',                           'bounds': {'min': 0, 'max': 5}},
  {'name': 'lambda',            'type': 'double',                           'bounds': {'min': 0, 'max': 10}},
  {'name': 'max_delta_step',    'type': 'double', 'transformation': 'log',  'bounds': {'min': 0.001, 'max': 10}},
  {'name': 'max_depth',         'type': 'int',                              'bounds': {'min': 2, 'max': 16}},
  {'name': 'min_child_weight',  'type': 'double',                           'bounds': {'min': 0, 'max': 10}},
  {'name': 'num_boost_round',   'type': 'int',                              'bounds': {'min': 10, 'max': 200}},
]
SEARCH_PARAMS = [param['name'] for param in SEARCH_BOUNDS]

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
PARAMETER_INFORMATION = {

  # Numerical Values
  'alpha':              {'type': 'double', 'limits':        [0, float("inf")],  'limits_type': ['closed', 'closed']},
  'colsample_bylevel':  {'type': 'double', 'limits':        [0, 1],             'limits_type': ['open', 'closed']},
  'colsample_bynode':   {'type': 'double', 'limits':        [0, 1],             'limits_type': ['open', 'closed']},
  'colsample_bytree':   {'type': 'double', 'limits':        [0, 1],             'limits_type': ['open', 'closed']},
  'eta':                {'type': 'double', 'limits':        [0, 1],             'limits_type': ['open', 'closed']},
  'gamma':              {'type': 'double', 'limits':        [0, float("inf")],  'limits_type': ['closed', 'closed']},
  'lambda':             {'type': 'double', 'limits':        [0, float("inf")],  'limits_type': ['closed', 'closed']},
  'max_delta_step':     {'type': 'int',    'limits':        [0, float("inf")],  'limits_type': ['closed', 'closed']},
  'max_depth':          {'type': 'int',    'limits':        [1, float("inf")],  'limits_type': ['closed', 'closed']},
  'max_leaves':         {'type': 'int',    'limits':        [1, float("inf")],  'limits_type': ['closed', 'closed']},
  'num_boost_round':    {'type': 'int',    'limits':        [1, float("inf")],  'limits_type': ['closed', 'closed']},
  'num_parallel_tree':  {'type': 'int',    'limits':        [1, float("inf")],  'limits_type': ['closed', 'closed']},
  'scale_pos_weight':   {'type': 'int',    'limits':        [0, float("inf")],  'limits_type': ['open', 'closed']},
  'sketch_eps':         {'type': 'double', 'limits':        [0, 1],             'limits_type': ['open', 'open']},
  'subsample':          {'type': 'double', 'limits':        [0, 1],             'limits_type': ['open', 'closed']},
  'refresh_leaf':       {'type': 'grid',   'grid_values':   [0, 1]},

  # String values
  'grow_policy':        {'type': 'string', 'string_values': ['depthwise', 'lossguide']},
  'predictor':          {'type': 'string', 'string_values': ['auto', 'cpu_predictor', 'gpu_predictor']},
  'process_type':       {'type': 'string', 'string_values': ['default', 'update']},
  'sampling_method':    {'type': 'string', 'string_values': ['uniform', 'gradient_based']},
  'tree_method':        {'type': 'string', 'string_values': ['auto', 'exact', 'approx', 'hist', 'gpu_hist']},
  'updater':            {'type': 'string', 'string_values': ['grow_colmaker', 'grow_histmaker', 'grow_local_histmaker',
                                                             'grow_quantile_histmaker', 'grow_gpu_hist', 'sync',
                                                             'refresh', 'prune']},
}
