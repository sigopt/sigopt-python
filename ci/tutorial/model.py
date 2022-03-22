# model.py  
import sklearn.datasets 
import sklearn.metrics 
from xgboost import XGBClassifier 
import sigopt 
 
# Data preparation required to run and evaluate the sample model 
X, y = sklearn.datasets.load_iris(return_X_y=True) 
Xtrain, ytrain = X[:100], y[:100] 

# Track the name of the dataset used for your Run 
sigopt.log_dataset('iris 2/3 training, full test') 
# Set n_estimators as the hyperparameter to explore for your Experiment 
sigopt.params.setdefault("n_estimators", 100) 
# Track the name of the model used for your Run 
sigopt.log_model('xgboost') 

# Instantiate and train your sample model 
model = XGBClassifier( 
  n_estimators=sigopt.params.n_estimators, 
  use_label_encoder=False, 
  eval_metric='logloss', 
) 
model.fit(Xtrain, ytrain) 
pred = model.predict(X) 

# Track the metric value and metric name for each Run 
sigopt.log_metric("accuracy", sklearn.metrics.accuracy_score(pred, y)) 
