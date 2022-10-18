# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from sigopt.orchestrate.lib.lists import *


class TestLists(object):
  def test_remove_nones(self):
    assert remove_nones([]) == []
    assert remove_nones([False, None, [], 0, {}]) == [False, [], 0, {}]
    assert remove_nones([False, None, [], 0, {}, 1, 2, 3, True, [1]]) == [False, [], 0, {}, 1, 2, 3, True, [1]]
    assert remove_nones({}) == {}
    assert remove_nones({
      'a': False,
      'b': None,
      'c': [],
      'd': 0,
      'e': {},
    }) == {
      'a': False,
      'c': [],
      'd': 0,
      'e': {},
    }
    assert remove_nones({
      'a': False,
      'b': None,
      'c': [],
      'd': 0,
      'e': {},
      'f': 1,
      'g': True,
    }) == {
      'a': False,
      'c': [],
      'd': 0,
      'e': {},
      'f': 1,
      'g': True,
    }
    assert remove_nones({
      'a': {
        'b': None,
      },
    }) == {
      'a': {
        'b': None,
      },
    }
    assert remove_nones(set((1, 'a', None))) == set((1, 'a'))
    assert remove_nones(set((1, 'a'))) == set((1, 'a'))
    assert remove_nones(set()) == set()

  def test_coalesce(self):
    assert coalesce() is None
    assert coalesce(None) is None
    assert coalesce(None, None) is None
    assert coalesce(None, None, None) is None
    assert coalesce(True) is True
    assert coalesce(False) is False
    assert coalesce(None, 1) == 1
    assert coalesce(None, 0) == 0
    assert coalesce(None, 0, 5) == 0
    assert coalesce(None, 1, 5) == 1

  def test_list_get(self):
    assert list_get([], 0) is None
    assert list_get([], 100) is None
    assert list_get([], -5) is None
    assert list_get([1], 0) == 1
    assert list_get([1], -1) == 1
    assert list_get([1], 100) is None
    assert list_get([1, 2, 3], 0) == 1
    assert list_get([1, 2, 3], 2) == 3
    assert list_get([1, 2, 3], -1) == 3
    assert list_get([1, 2, 3], -3) == 1
    assert list_get([1, 2, 3], 100) is None

  def test_partition(self):
    assert partition([], lambda x: True) == ([], [])
    assert partition([], lambda x: False) == ([], [])
    assert partition([1, 2], lambda x: True) == ([1, 2], [])
    assert partition([1, 2], lambda x: False) == ([], [1, 2])
    assert partition([1, 2, 3, 4], lambda x: x % 2 == 0) == ([2, 4], [1, 3])
    assert partition((i for i in range(1, 5)), lambda x: x % 2 == 0) == ([2, 4], [1, 3])
