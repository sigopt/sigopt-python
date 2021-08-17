import pytest
from click.testing import CliRunner
from mock import patch

from sigopt.cli import cli
from sigopt.orchestrate.paths import get_executable_path


class TestClusterKubectlCli(object):
  @pytest.mark.parametrize("arguments", [
    (),
    ("-h",),
    ("--help",),
    ("--help",),
    ("get", "--help"),
    ("exec", "-ti", "po/helloworld", "--", "/bin/sh"),
  ])
  def test_cluster_kubectl_command(self, arguments):
    kubectl_env_dict = {
      'KUBECONFIG': 'dummy_kubeconfig',
      'PATH': '/dummy/bin',
    }
    runner = CliRunner()
    with \
      patch('os.execvpe') as mock_execvpe, \
      patch('sigopt.orchestrate.kubectl.service.KubectlService.kubectl_env', side_effect=kubectl_env_dict), \
      patch('sigopt.orchestrate.cluster.service.ClusterService.assert_is_connected', return_value='foobar'):
      result = runner.invoke(cli, ["cluster", "kubectl", *arguments])
      raise Exception(str(result))
      exec_path = get_executable_path('kubectl')
      assert mock_execvpe.called_once_with(
        exec_path,
        [exec_path, *arguments],
        env=kubectl_env_dict,
      )
    assert result.exit_code == 0
