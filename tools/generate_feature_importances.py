import sigopt
from sigopt.interface import get_connection
from sigopt.run_context import RunContext
import string
import numpy as np
import sys

def switch_run_context(run_id):
  context = RunContext(
    connection = get_connection(),
    run = sigopt.get_run(run_id))
  sigopt._global_run_context._run_context = context

def rand_str(n, chars=string.ascii_letters + string.digits):
  chars = np.array(list(chars))
  idx = np.random.choice(len(chars), n)
  return ''.join(chars[idx])

def generate_feature_importances(num_feature=50, max_feature_len=100, score_type='exp'):
  lens = np.random.choice(np.arange(1, max_feature_len + 1), num_feature)
  features = [rand_str(n) for n in lens]
  scores = np.random.uniform(size=num_feature)
  if score_type == 'exp':
    scores = np.exp((scores - 0.5) * 10)
  return {
    'type': 'weight',
    'scores': dict(zip(features, scores))
  }

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--run', default=19, help='run id')
  parser.add_argument('--score_type', default='exp', help='score type')
  parser.add_argument('--num_feature', default=50, help='number of defauts')
  parser.add_argument('--max_feature_length', default=100, help='max feature name length')
  args = parser.parse_args()
  switch_run_context(args.run)
  fp = generate_feature_importances(args.num_feature, args.max_feature_length, args.score_type)
  sigopt._global_run_context.log_sys_metadata('feature_importances', fp)
