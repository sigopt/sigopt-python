import mock
import pytest
import warnings

from sigopt.endpoint import BoundApiEndpoint
from sigopt.objects import *

warnings.simplefilter("error")

class TestPagination(object):
  @pytest.fixture(autouse=True)
  def set_warnings(self):
    warnings.simplefilter("error")

  @pytest.fixture
  def experiment1(self):
    return Experiment({'object': 'experiment'})

  @pytest.fixture
  def experiment2(self):
    return Experiment({'object': 'experiment', 'type': 'offline'})

  @pytest.fixture
  def bound_endpoint(self, experiment2, no_paging):
    second_page = Pagination(Experiment, {
      'object': 'pagination',
      'count': 2,
      'data': [experiment2.to_json()],
      'paging': no_paging,
    })
    return mock.Mock(BoundApiEndpoint, side_effect=lambda *args, **kwargs: second_page)

  def test_empty(self, bound_endpoint):
    assert list(Pagination(Experiment, {}, bound_endpoint, {}).iterate_pages()) == []
    assert bound_endpoint.mock_calls == []

  @pytest.fixture
  def no_paging(self):
    return dict(before=None, after=None)

  @pytest.fixture(params=[
    dict(before='1', after='2'),
    dict(after='2'),
  ])
  def backward_paging(self, request):
    return request.param

  @pytest.fixture(params=[
    dict(before='1', after=None),
    dict(before='1', after='2'),
  ])
  def forward_paging(self, request):
    return request.param

  def test_single_page(self, experiment1, bound_endpoint, no_paging):
    assert list(Pagination(Experiment, {
      'object': 'pagination',
      'count': 1,
      'data': [experiment1.to_json()],
      'paging': no_paging,
    }, bound_endpoint, {}).iterate_pages()) == [experiment1]
    assert bound_endpoint.mock_calls == []

  def make_call(self, paging, bound_endpoint, retrieve_params):
    list(Pagination(Experiment, {
      'object': 'pagination',
      'count': 1,
      'data': [{'object': 'experiment'}],
      'paging': paging,
    }, bound_endpoint, retrieve_params).iterate_pages())

  def test_next_page(self, experiment1, experiment2, bound_endpoint, forward_paging):
    assert list(Pagination(Experiment, {
      'object': 'pagination',
      'count': 1,
      'data': [experiment1.to_json()],
      'paging': forward_paging,
    }, bound_endpoint, {}).iterate_pages()) == [experiment1, experiment2]
    assert len(bound_endpoint.mock_calls) == 1

  def test_receive_after_doesnt_page(self, experiment1, experiment2, bound_endpoint, backward_paging):
    assert list(Pagination(Experiment, {
      'object': 'pagination',
      'count': 1,
      'data': [experiment1.to_json()],
      'paging': {'after': '2'},
    }, bound_endpoint, {}).iterate_pages()) == [experiment1]
    assert len(bound_endpoint.mock_calls) == 0

  def test_retrieve_params(self, bound_endpoint, forward_paging):
    self.make_call(
      retrieve_params={'state': 'all'},
      paging=forward_paging,
      bound_endpoint=bound_endpoint,
    )
    assert len(bound_endpoint.mock_calls) == 1
    assert bound_endpoint.call_args[1]['state'] == 'all'

  def test_iterate_pages_before_returns_before(self, bound_endpoint):
    self.make_call(
      retrieve_params={'before': '888'},
      paging={'before': '1', 'after': None},
      bound_endpoint=bound_endpoint,
    )
    assert len(bound_endpoint.mock_calls) == 1
    assert bound_endpoint.call_args[1].get('before') == '1'
    assert bound_endpoint.call_args[1].get('after') is None

  def test_iterate_pages_before_returns_after(self, bound_endpoint):
    self.make_call(
      retrieve_params={'before': '888'},
      paging={'before': None, 'after': '2'},
      bound_endpoint=bound_endpoint,
    )
    assert len(bound_endpoint.mock_calls) == 0

  def test_iterate_pages_before_returns_both(self, bound_endpoint):
    self.make_call(
      retrieve_params={'before': '888'},
      paging={'before': '1', 'after': '2'},
      bound_endpoint=bound_endpoint,
    )
    assert bound_endpoint.call_args[1].get('before') == '1'
    assert bound_endpoint.call_args[1].get('after') is None

  def test_iterate_pages_after_returns_before(self, bound_endpoint):
    self.make_call(
      retrieve_params={'after': '999'},
      paging={'before': '1', 'after': None},
      bound_endpoint=bound_endpoint,
    )
    assert len(bound_endpoint.mock_calls) == 0

  def test_iterate_pages_after_returns_after(self, bound_endpoint):
    self.make_call(
      retrieve_params={'after': '999'},
      paging={'before': None, 'after': '2'},
      bound_endpoint=bound_endpoint,
    )
    assert len(bound_endpoint.mock_calls) == 1
    assert bound_endpoint.call_args[1].get('before') is None
    assert bound_endpoint.call_args[1].get('after') == '2'

  def test_iterate_pages_after_returns_both(self, bound_endpoint):
    self.make_call(
      retrieve_params={'after': '999'},
      paging={'before': '1', 'after': '2'},
      bound_endpoint=bound_endpoint,
    )
    assert len(bound_endpoint.mock_calls) == 1
    assert bound_endpoint.call_args[1].get('before') is None
    assert bound_endpoint.call_args[1].get('after') == '2'

  def test_iterate_pages_before_after_returns_before(self, bound_endpoint):
    self.make_call(
      retrieve_params={'before': '999', 'after': '888'},
      paging={'before': '1', 'after': None},
      bound_endpoint=bound_endpoint,
    )
    assert len(bound_endpoint.mock_calls) == 1
    assert bound_endpoint.call_args[1].get('before') == '1'
    assert bound_endpoint.call_args[1].get('after') is None

  def test_iterate_pages_before_after_returns_after(self, bound_endpoint):
    self.make_call(
      retrieve_params={'before': '999', 'after': '888'},
      paging={'before': None, 'after': '2'},
      bound_endpoint=bound_endpoint,
    )
    assert len(bound_endpoint.mock_calls) == 0

  def test_iterate_pages_before_after_returns_both(self, bound_endpoint):
    self.make_call(
      retrieve_params={'before': '999', 'after': '888'},
      paging={'before': '1', 'after': '2'},
      bound_endpoint=bound_endpoint,
    )
    assert len(bound_endpoint.mock_calls) == 1
    assert bound_endpoint.call_args[1].get('before') == '1'
    assert bound_endpoint.call_args[1].get('after') is None

  def test_lazy_iterator(self, experiment1, bound_endpoint, forward_paging):
    iterator = Pagination(Experiment, {
      'object': 'pagination',
      'count': 1,
      'data': [experiment1.to_json()],
      'paging': forward_paging,
    }, bound_endpoint, {}).iterate_pages()
    assert len(bound_endpoint.mock_calls) == 0
    list(iterator)
    assert len(bound_endpoint.mock_calls) == 1

  def test_paging_before_precedence_rules_forward(self, experiment1, bound_endpoint, forward_paging):
    list(Pagination(Experiment, {
      'object': 'pagination',
      'count': 1,
      'data': [experiment1.to_json()],
      'paging': forward_paging,
    }, bound_endpoint, {'before': '1'}).iterate_pages())
    assert len(bound_endpoint.mock_calls) == 1
    assert bound_endpoint.call_args[1]['before'] == '1'
    assert 'after' not in bound_endpoint.call_args[1]

  def test_paging_before_precedence_rules_backward(self, experiment1, bound_endpoint):
    list(Pagination(Experiment, {
      'object': 'pagination',
      'count': 1,
      'data': [experiment1.to_json()],
      'paging': {'after': '2'},
    }, bound_endpoint, {'before': '1'}).iterate_pages())
    assert len(bound_endpoint.mock_calls) == 0

  def test_paging_after_precedence_rules_forward(self, experiment1, bound_endpoint):
    list(Pagination(Experiment, {
      'object': 'pagination',
      'count': 1,
      'data': [experiment1.to_json()],
      'paging': {'before': '1'},
    }, bound_endpoint, {'after': '2'}).iterate_pages())
    assert len(bound_endpoint.mock_calls) == 0

  def test_paging_after_precedence_rules_backward(self, experiment1, bound_endpoint, backward_paging):
    list(Pagination(Experiment, {
      'object': 'pagination',
      'count': 1,
      'data': [experiment1.to_json()],
      'paging': backward_paging,
    }, bound_endpoint, {'after': '2'}).iterate_pages())
    assert len(bound_endpoint.mock_calls) == 1
    assert 'before' not in bound_endpoint.call_args[1]
    assert bound_endpoint.call_args[1]['after'] == '2'

  def test_paging_before_and_after_precedence_rules(self, experiment1, bound_endpoint):
    list(Pagination(Experiment, {
      'object': 'pagination',
      'count': 1,
      'data': [experiment1.to_json()],
      'paging': {'before': '1', 'after': '2'},
    }, bound_endpoint, {}).iterate_pages())
    assert len(bound_endpoint.mock_calls) == 1
    assert bound_endpoint.call_args[1]['before'] == '1'
    assert 'after' not in bound_endpoint.call_args[1]
