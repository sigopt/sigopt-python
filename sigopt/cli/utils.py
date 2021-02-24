import git
import os
import signal
import subprocess
import sys
import threading
from git.exc import InvalidGitRepositoryError

from ..config import config
from ..vendored import six


class StreamThread(threading.Thread):
  def __init__(self, input_stream, output_stream):
    super(StreamThread, self).__init__()
    self.input_stream = input_stream
    self.output_stream = output_stream
    self.buffer = six.StringIO()
    self.lock = threading.Lock()

  def read_input_line(self):
    with self.lock:
      return self.input_stream.readline()

  def run(self):
    for line in iter(self.read_input_line, ''.encode()):
      try:
        data = line.decode('utf-8', 'strict')
      except UnicodeDecodeError:
        data = 'Failed to decode binary data to utf-8'
      finally:
        self.buffer.write(data)
        self.output_stream.write(data)

  def stop(self):
    with self.lock:
      self.input_stream.close()
    self.join()
    return self.buffer.getvalue()

def maybe_truncate_log(log_content):
  # If log content is extremely long, preserve some useful content instead of failing.
  # TODO(patrick): Support streaming logs to avoid this
  max_size = 1024 * 1024
  if len(log_content) >= max_size:
    truncated_disclaimer = '[ WARNING ] The max size has been reached so these logs have been truncated'
    half = max_size // 2
    head = log_content[:half]
    tail = log_content[-half:]
    log_content = '\n\n'.join([
      truncated_disclaimer,
      head,
      '... truncated ...',
      tail,
    ])
  return log_content

def get_git_hexsha():
  repo = git.Repo(search_parent_directories=True)
  return repo.head.object.hexsha

def get_subprocess_environment(env=None):
  ret = os.environ.copy()
  ret.update(config.get_environment_context())
  ret.update(env or {})
  return ret

def run_subprocess(run_context, entrypoint, entrypoint_args, env=None):
  cmd = [sys.executable, entrypoint] + list(entrypoint_args)
  return run_subprocess_command(run_context, cmd=cmd, env=env)

def run_subprocess_command(run_context, cmd, env=None):
  env = get_subprocess_environment(env)
  proc_stdout, proc_stderr = subprocess.PIPE, subprocess.PIPE
  proc = subprocess.Popen(
    cmd,
    env=env,
    stdout=proc_stdout,
    stderr=proc_stderr,
  )
  stdout, stderr = StreamThread(proc.stdout, sys.stdout), StreamThread(proc.stderr, sys.stderr)
  stdout.start()
  stderr.start()
  return_code = 0
  try:
    return_code = proc.wait()
  except KeyboardInterrupt:
    os.kill(proc.pid, signal.SIGINT)
    proc.wait()
    raise
  finally:
    stdout_content, stderr_content = stdout.stop(), stderr.stop()
    if config.log_collection_enabled:
      run_context.update_logs({
        'stdout': {'content': maybe_truncate_log(stdout_content)},
        'stderr': {'content': maybe_truncate_log(stderr_content)},
      })
  if return_code > 0:
    raise subprocess.CalledProcessError(return_code, cmd)

def run_notebook(entrypoint):
  return subprocess.check_output(
    [
      'jupyter', 'nbconvert',
      '--ExecutePreprocessor.timeout=-1',
      '--execute',
      '--stdout',
      '--no-prompt',
      '--no-input',
      '--to=python',
      entrypoint,
    ],
    env=get_subprocess_environment(),
  )

def run_user_program(run_factory, entrypoint, entrypoint_args, user_provided_name=None, suggestion=None):
  with run_factory.create_global_run(name=user_provided_name, suggestion=suggestion) as run_context:
    if config.code_tracking_enabled:
      source_code = {}
      with open(entrypoint) as entrypoint_fp:
        source_code['content'] = entrypoint_fp.read()
      try:
        source_code['hash'] = get_git_hexsha()
      except InvalidGitRepositoryError:
        pass
      run_context.log_source_code(**source_code)
    if entrypoint.endswith('.ipynb'):
      if entrypoint_args:
        raise Exception('Command line arguments cannot be passed to notebooks')
      # TODO(patrick): The output of this command should be the tracked code (or logs? It's kind of both)
      run_notebook(entrypoint)
    else:
      run_subprocess(run_context, entrypoint, entrypoint_args)

def check_path(entrypoint, error_msg):
  if not os.path.isfile(entrypoint):
    raise Exception(error_msg)

def setup_cli():
  config.set_user_agent_info(['CLI'])
