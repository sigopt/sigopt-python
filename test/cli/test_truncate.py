from sigopt.run_context import maybe_truncate_log


def test_short_logs_dont_get_truncated():
  short_logs = 'hello there\n'
  content = maybe_truncate_log(short_logs)
  assert content == short_logs

def test_long_logs_get_truncated():
  max_size = 1024
  long_logs = 'a' * (max_size * 2) + '\n'
  content = maybe_truncate_log(long_logs)
  assert max_size < len(content) < max_size * 2
  assert content.startswith('[ WARNING ] ')
  assert '... truncated ...'  in content
  assert content.endswith('aaaa\n')
