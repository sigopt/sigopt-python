import pytest
from mock import MagicMock, Mock

from sigopt.orchestrate.job_status.service import JobStatusService


class TestJobStatusService(object):
  @pytest.fixture
  def mock_sigopt_experiment(self):
    return Mock(
      name='my experiment',
      budget=50,
      progress=Mock(total_run_count=100),
    )

  @pytest.fixture
  def services(self, mock_sigopt_experiment):
    return Mock(
      sigopt_service=Mock(safe_fetch_experiment=Mock(return_value=mock_sigopt_experiment))
    )

  @pytest.fixture
  def mock_job(self):
    mock = MagicMock()
    mock.metadata.name = 'job'
    mock.status.conditions = None
    return mock

  @pytest.fixture
  def job_status_service(self, services):
    return JobStatusService(services)

  def test_parse_job_no_conditions(self, job_status_service, mock_job):
    job_status_service.parse_job(mock_job)

  @pytest.mark.parametrize('conditions,expected_status', [
    ([], 'Not Complete'),
    ([dict(status='True', type='Complete')], 'Complete'),
    ([dict(status='False', type='Complete')], 'Not Complete'),
    ([dict(status='Unknown', type='Complete')], 'Maybe Complete'),
    ([
      dict(status='True', type='Foo'),
      dict(status='False', type='Bar'),
      dict(status='Unknown', type='Baz'),
    ], 'Foo, Not Bar, Maybe Baz'),
  ])
  def test_parse_job_conditions(self, job_status_service, mock_job, conditions, expected_status):
    mock_conditions = []
    for c in conditions:
      mock_conditions.append(self.get_condition_mock(c['status'], c['type']))
    mock_job.status.conditions = mock_conditions
    assert job_status_service.parse_job(mock_job)['status'] == expected_status

  def get_condition_mock(self, status, cond_type):
    mock = Mock()
    mock.status = status
    mock.type = cond_type
    return mock
