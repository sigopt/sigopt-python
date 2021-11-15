import sigopt
import string
import numpy as np
import sys

def rand_str(n, chars=string.ascii_letters + string.digits):
  chars = np.array(list(chars))
  idx = np.random.choice(len(chars), n)
  return ''.join(chars[idx])

def generate_feature_importances(num_feature=50, max_feature_len=100, score_type='exp'):
  features = [rand_str(n) for n in range(1, num_feature)]
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
  sigopt.switch_run_context(args.run)
  fp = generate_feature_importances(args.num_feature, args.max_feature_length, args.score_type)
  sigopt.log_sys_metadata('feature_importances', fp)
