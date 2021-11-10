import platform
import random

import sigopt.xgboost
from sigopt.xgboost.run import PARAMS_LOGGED_AS_METADATA
from sklearn import datasets
from sklearn.model_selection import train_test_split
import xgboost as xgb
import numpy as np

iris = datasets.load_iris()
X = iris.data
y = iris.target
num_class = 3
X_train, X_test, Y_train, Y_test = train_test_split(X, y, test_size=0.2)
D_train = xgb.DMatrix(X_train, label=Y_train)
D_test = xgb.DMatrix(X_test, label=Y_test)

params = {
  'num_class': num_class,
  'lambda': 1,
}


experiment_config = dict(
  name="Single metric optimization",
  type="offline",
  parameters=[
    dict(
      name="eta",
      type="double",
      bounds=dict(
        min=0.1,
        max=0.5
      )
    ),
    dict(
      name="max_depth",
      type="int",
      bounds=dict(
        min=2,
        max=8
      )
    )
  ],
  metrics=[
    dict(
      name="accuracy",
      strategy="optimize",
      objective="maximize"
    )
  ],
  parallel_bandwidth=1,
  budget=2
)
sigopt.xgboost.experiment(experiment_config, D_train, [(D_test, 'TestSet')], params, num_boost_round=5, run_options=None)
