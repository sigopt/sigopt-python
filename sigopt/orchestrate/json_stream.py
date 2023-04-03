# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import json


class JsonBuffer:
  def __init__(self):
    self.buffer = []

  def consume(self, chunk):
    if isinstance(chunk, bytes):
      chunk = chunk.decode("utf-8")
    self.buffer.append(chunk)
    return self.emit_data()

  def emit_data(self):
    parts = "".join(self.buffer).splitlines(True)
    if not parts:
      return []
    if parts[-1] and parts[-1][-1] != "\n":
      # NOTE(taylor): the last line is not a whole line and should be buffered
      self.buffer = [parts[-1]]
      parts = parts[:-1]
    else:
      self.buffer = []
    return [json.loads(part) for part in parts if part.strip()]


def json_stream(stream):
  json_buffer = JsonBuffer()
  for chunk in stream:
    yield from json_buffer.consume(chunk)
