SEARCH_BOUNDS = [
  {'name': 'num_boost_round',   'type': 'int',                              'bounds': {'min': 10, 'max': 200}},
  {'name': 'eta',               'type': 'double', 'transformation': 'log',  'bounds': {'min': 0.001, 'max': 1}},
  {'name': 'gamma',             'type': 'double',                           'bounds': {'min': 0, 'max': 5}},
  {'name': 'max_depth',         'type': 'int',                              'bounds': {'min': 2, 'max': 16}},
  {'name': 'lambda',            'type': 'double',                           'bounds': {'min': 0, 'max': 10}},
  {'name': 'alpha',             'type': 'double',                           'bounds': {'min': 0, 'max': 10}},
  {'name': 'min_child_weight',  'type': 'double',                           'bounds': {'min': 0, 'max': 10}},
  {'name': 'max_delta_step',    'type': 'double', 'transformation': 'log',  'bounds': {'min': 0.001, 'max': 10}}
]
SEARCH_PARAMS = [param['name'] for param in SEARCH_BOUNDS]
DEFAULT_SEARCH_PARAMS = ['num_boost_round', 'eta', 'gamma', 'max_depth', 'min_child_weight']
DEFAULT_CLASSIFICATION_METRICS = ['accuracy', 'precision', 'recall', 'F1']
DEFAULT_REGRESSION_METRICS = ['mean absolute error', 'mean squared error']
SUPPORTED_METRICS_TO_OPTIMIZE = DEFAULT_CLASSIFICATION_METRICS + DEFAULT_REGRESSION_METRICS
DEFAULT_NUM_BOOST_ROUND = 10
DEFAULT_BO_ITERATIONS = 2
