import xgboost as xgb
from sklearn import datasets
from sklearn.model_selection import train_test_split
import os
from pprint import pprint
import json
import numpy as np

# Load data
iris = datasets.load_iris()
X = iris.data
y = iris.target
num_class = len(np.unique(y))
X_train, X_test, Y_train, Y_test = train_test_split(X, y, test_size=0.2)
D_train = xgb.DMatrix(X_train, label=Y_train)
D_test = xgb.DMatrix(X_test, label=Y_test)

xgb_params = dict(
  params={
    'max_depth': 7,
    'num_class': num_class,
    'objective': 'multi:softmax',
    'tree_method': 'hist',
    'eval_metric': ['mlogloss', 'merror']
  },
  dtrain=D_train,
  evals=[(D_test, 'test0'), (D_test, 'test1')],
  num_boost_round=3,
)

def train_predict_save():
  model = xgb.train(**xgb_params)
  preds = model.predict(D_test)
  model.save_model('0001.model')
  return model

if __name__ == '__main__':
  train_predict_save()
