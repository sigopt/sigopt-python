# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import errno
import io
import os
import shlex
import signal
import subprocess  # nosec
import sys
import threading

import click

from sigopt.factory import SigOptFactory
from sigopt.sigopt_logging import enable_print_logging, print_logger
from sigopt.run_context import GlobalRunContext

from .arguments.load_yaml import ValidatedData


class StreamThread(threading.Thread):
  def __init__(self, input_stream, output_stream):
    super().__init__()
    self.input_stream = input_stream
    self.output_stream = output_stream
    self.buffer = io.StringIO()
    self.lock = threading.Lock()

  def read_input_line(self):
    try:
      with self.lock:
        return self.input_stream.readline()
    except ValueError as ve:
      raise StopIteration() from ve

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

def get_subprocess_environment(config, run_context, env=None):
  config.set_context_entry(GlobalRunContext(run_context))
  ret = os.environ.copy()
  ret.update(config.get_environment_context())
  ret.update(env or {})
  return ret

def run_subprocess(config, run_context, commands, env=None):
  return run_subprocess_command(config, run_context, cmd=commands, env=env)

def run_subprocess_command(config, run_context, cmd, env=None):
  env = get_subprocess_environment(config, run_context, env)
  proc_stdout, proc_stderr = subprocess.PIPE, subprocess.PIPE
  try:
    proc = subprocess.Popen(
      cmd,
      env=env,
      stdout=proc_stdout,
      stderr=proc_stderr,
    )
  except OSError as ose:
    msg = str(ose)
    is_fnfe = isinstance(ose, FileNotFoundError)
    is_eacces = ose.errno == errno.EACCES
    if is_fnfe or is_eacces and os.path.exists(ose.filename):
      is_full_path = ose.filename.startswith("/") or ose.filename.startswith("./")
      is_executable = os.access(ose.filename, os.X_OK)
      is_py = ose.filename.endswith(".py")
      is_sh = ose.filename.endswith(".sh") or ose.filename.endswith(".bash")
      if is_fnfe and not is_full_path and is_executable:
        msg += "\nPlease prefix your script with `./`, ex:"
        msg += "\n$ sigopt SUBCOMMAND -- ./{ose.filename} {shlex.join(cmd[1:])}"
      elif is_py and not is_executable:
        msg += "\nPlease include the python executable when running python files, ex:"
        msg += f"\n$ sigopt SUBCOMMAND -- python {shlex.join(cmd)}"
      elif is_sh and not is_executable:
        msg += f"\nPlease make your shell script executable, ex:\n$ chmod +x {ose.filename}"
    raise click.ClickException(msg) from ose
  stdout, stderr = StreamThread(proc.stdout, sys.stdout), StreamThread(proc.stderr, sys.stderr)
  stdout.start()
  stderr.start()
  return_code = 0
  try:
    return_code = proc.wait()
  except KeyboardInterrupt:
    try:
      os.kill(proc.pid, signal.SIGINT)
    except ProcessLookupError:
      pass
    proc.wait()
    raise
  finally:
    stdout_content, stderr_content = stdout.stop(), stderr.stop()
    if config.log_collection_enabled:
      run_context.set_logs({
        'stdout': stdout_content,
        'stderr': stderr_content,
      })
  return return_code

def run_user_program(config, run_context, commands, source_code_content):
  source_code = {}
  git_hash = get_git_hexsha()
  if git_hash:
    source_code['hash'] = git_hash
  if source_code_content is not None:
    source_code['content'] = source_code_content
  run_context.log_source_code(**source_code)
  exit_code = run_subprocess(config, run_context, commands)
  if exit_code != 0:
    print_logger.error("command exited with non-zero status: %s", exit_code)
  return exit_code

def setup_cli(config):
  config.set_user_agent_info(['CLI'])
  enable_print_logging()

def create_aiexperiment_from_validated_data(experiment_file, project):
  assert isinstance(experiment_file, ValidatedData)
  factory = SigOptFactory(project)
  return factory.create_prevalidated_aiexperiment(experiment_file.data)

def cli_experiment_loop(config, experiment, command, run_options, source_code_content):
  for run_context in experiment.loop(name=run_options.get("name")):
    with run_context:
      run_user_program(config, run_context, command, source_code_content)
