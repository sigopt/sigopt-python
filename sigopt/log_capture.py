# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import io
import sys
import threading

from .decorators import public


class MonitorStream(io.IOBase):
  def __init__(self, original_stream):
    super().__init__()
    self.buffer_lock = threading.Lock()
    self.original_stream = original_stream
    self.buffer_stream = None
    self._replace_buffer_stream()

  def _replace_buffer_stream(self):
    self.buffer_stream = io.StringIO()

  @public
  def close(self):
    raise IOError("MonitorStream cannot be closed")

  @public
  @property
  def closed(self):
    return self.original_stream.closed

  @public
  def fileno(self):
    raise IOError("MonitorStream has no fileno")

  @public
  def flush(self):
    return self.original_stream.flush()

  @public
  def isatty(self):
    return False

  @public
  def readable(self):
    return False

  @public
  def readline(self, *args, **kwargs):
    return self.original_stream.readline(*args, **kwargs)

  @public
  def readlines(self, *args, **kwargs):
    return self.original_stream.readlines(*args, **kwargs)

  @public
  def seek(self, *args, **kwargs):
    raise IOError("MonitorStream is not seekable")

  @public
  def seekable(self):
    return False

  @public
  def tell(self, *args, **kwargs):
    raise IOError("MonitorStream is not seekable")

  @public
  def writable(self):
    return True

  @public
  def write(self, content):
    rval = self.original_stream.write(content)
    with self.buffer_lock:
      self.buffer_stream.write(content)
    return rval

  @public
  def writelines(self, lines):
    for line in lines:
      self.write(line)

  def get_buffer_contents(self):
    with self.buffer_lock:
      content = self.buffer_stream.getvalue()
      self._replace_buffer_stream()
    return content


class BaseStreamMonitor(object):
  def get_stream_data(self):
    raise NotImplementedError()

  def __enter__(self):
    raise NotImplementedError()

  def __exit__(self, typ, value, trace):
    del trace
    raise NotImplementedError()


class NullStreamMonitor(BaseStreamMonitor):
  def get_stream_data(self):
    return None

  def __enter__(self):
    return self

  def __exit__(self, typ, value, trace):
    del trace


class SystemOutputStreamMonitor(BaseStreamMonitor):
  def __init__(self):
    super().__init__()
    self.monitor_streams = None

  def get_stream_data(self):
    if self.monitor_streams is None:
      return None
    stdout_content, stderr_content = (monitor_stream.get_buffer_contents() for monitor_stream in self.monitor_streams)
    return stdout_content, stderr_content

  def __enter__(self):
    if self.monitor_streams is not None:
      raise Exception("Already monitoring")
    self.monitor_streams = MonitorStream(sys.stdout), MonitorStream(sys.stderr)
    sys.stdout, sys.stderr = self.monitor_streams
    return self

  def __exit__(self, typ, value, trace):
    del trace
    sys.stdout, sys.stderr = (monitor_stream.original_stream for monitor_stream in self.monitor_streams)
