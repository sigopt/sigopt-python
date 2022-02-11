from sigopt.local_run_context import LocalRunContext
import pytest


class TestLocalRunContext(object):

  @pytest.fixture
  def context(self):
    return LocalRunContext()

  @pytest.fixture
  def params(self):
    return {
      'x': 1.0,
      'y': 2.0
    }

  @pytest.fixture
  def metrics(self):
    return {
      'v0': 1,
      'v1': 2.0,
    }

  def test_init(self):
    name = 'test0'
    metadata = {'m0': 1, 'm2': 2.0}
    context = LocalRunContext(name=name, metadata=metadata)
    run = context.get()
    assert run['name'] == name
    assert run['metadata'] == metadata

  @pytest.mark.parametrize('state', ['completed', 'failed'])
  def test_log_state(self, context, state):
    context.log_state(state)
    run = context.get()
    assert run['state'] == state

  def test_log_failure(self, context):
    context.log_failure()
    run = context.get()
    assert run['state'] == 'failed'

  def test_log_metrics(self, context, metrics):
    context.log_metrics()
    run = context.get()
    run['values'] == metrics

  @pytest.mark.parametrize('source, source_sort, source_default_show', [
    ('s0', 10, True),
    ('s0', 20, False),
    ('s0', None, None),
    (None, 20, False),
  ])
  def test_log_parameters(self, context, params, source, source_sort, source_default_show):
    if source_sort is not None:
      source_meta = {'sort': source_sort, 'default_show': source_default_show}
    else:
      source_meta = None
    context.log_parameters(params, source, source_meta)
    run = context.get()
    assert run['assignments'] == params
    if source is not None:
      assert run['assignments_meta'] == {p: {'source': source} for p in params}
      if source_sort is not None:
        assert run['assignments_sources'][source] == {'sort': source_sort, 'default_show': source_default_show}
      else:
        assert 'assignments_sources' not in run
    else:
      assert 'assignments_meta' not in run and 'assignments_sources' not in run
