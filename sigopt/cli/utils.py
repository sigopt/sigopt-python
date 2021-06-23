import os
import signal
import subprocess
import sys
import threading

from ..logging import enable_print_logger
from ..run_context import GlobalRunContext
from ..vendored import six


class StreamThread(threading.Thread):
  def __init__(self, input_stream, output_stream):
    super(StreamThread, self).__init__()
    self.input_stream = input_stream
    self.output_stream = output_stream
    self.buffer = six.StringIO()
    self.lock = threading.Lock()

  def read_input_line(self):
    try:
      with self.lock:
        return self.input_stream.readline()
    except ValueError:
      raise StopIteration()

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

def get_git_hexsha():
  try:
    import git
    from git.exc import InvalidGitRepositoryError
  except ImportError:
    return None
  try:
    repo = git.Repo(search_parent_directories=True)
    return repo.head.object.hexsha
  except InvalidGitRepositoryError:
    return None

def get_subprocess_environment(config, env=None):
  ret = os.environ.copy()
  ret.update(config.get_environment_context())
  ret.update(env or {})
  return ret

def run_subprocess(config, run_context, entrypoint, entrypoint_args, env=None):
  cmd = [sys.executable, entrypoint] + list(entrypoint_args)
  return run_subprocess_command(config, run_context, cmd=cmd, env=env)

def run_subprocess_command(config, run_context, cmd, env=None):
  env = get_subprocess_environment(config, env)
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
      run_context.set_logs({
        'stdout': stdout_content,
        'stderr': stderr_content,
      })
  if return_code > 0:
    raise subprocess.CalledProcessError(return_code, cmd)

def run_notebook(config, entrypoint):
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
    env=get_subprocess_environment(config),
  )

def run_user_program(config, run_context, entrypoint, entrypoint_args):
  if config.code_tracking_enabled:
    source_code = {}
    with open(entrypoint) as entrypoint_fp:
      source_code['content'] = entrypoint_fp.read()
      git_hash = get_git_hexsha()
      if git_hash:
        source_code['hash'] = git_hash
    run_context.log_source_code(**source_code)
  global_run_context = GlobalRunContext(run_context)
  config.set_context_entry(global_run_context)
  if entrypoint.endswith('.ipynb'):
    if entrypoint_args:
      raise Exception('Command line arguments cannot be passed to notebooks')
    # TODO(patrick): The output of this command should be the tracked code (or logs? It's kind of both)
    run_notebook(config, entrypoint)
  else:
    run_subprocess(config, run_context, entrypoint, entrypoint_args)

def check_path(entrypoint, error_msg):
  if not os.path.isfile(entrypoint):
    raise Exception(error_msg)

def setup_cli(config):
  config.set_user_agent_info(['CLI'])
  enable_print_logger()
