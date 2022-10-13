# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import pytest

from sigopt.defaults import normalize_project_id


@pytest.mark.parametrize('project_id,expected', [
  ('simple', 'simple'),
  ('CAPS', 'caps'),
  ('CamelCase', 'camelcase'),
  ('snake_case', 'snake_case'),
  ('numbers0123', 'numbers0123'),
  ('h-yphen', 'h-yphen'),
  ("that's`~!@#$%^&*()+[]{};:'\",<>/?illegal!", 'thatsillegal'),
])
def test_normalize_project_id(project_id, expected):
  normalized = normalize_project_id(project_id)
  assert normalized == expected
