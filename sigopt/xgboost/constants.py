DEFAULT_EVALS_NAME = 'TestSet'
DEFAULT_TRAINING_NAME = 'TrainingSet'
USER_SOURCE_NAME = 'User Specified'

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
