import json
import random
import string

from ..docker.service import DockerService
from ..exceptions import OrchestrateException
from ..services.base import Service
from ..version import DEFAULT_CONTROLLER_IMAGE


def format_k8s_env_vars(env_vars):
  return [
    dict(name=key, value=value)
    for key, value in env_vars.items()
  ]

class JobRunnerService(Service):
  DEFAULT_EPHEMERAL_STORAGE_REQUEST = "128Mi"
  EXPERIMENT_ENV_KEY = "ORCHESTRATE_EXPERIMENT_ID"

  def sigopt_env_vars(self):
    client, project = self.services.sigopt_service.ensure_project_exists()
    return format_k8s_env_vars({
      'SIGOPT_API_TOKEN': self.services.sigopt_service.api_token,
      'SIGOPT_API_URL': self.services.sigopt_service.api_url,
      'SIGOPT_PROJECT': project,
      'SIGOPT_CLIENT': client,
    })

  def format_resources(self, resource_options):
    resource_options = resource_options or {}
    requests = resource_options.setdefault("requests", {})
    requests.setdefault("ephemeral-storage", self.DEFAULT_EPHEMERAL_STORAGE_REQUEST)
    limits = resource_options.setdefault("limits", {})

    if resource_options.get('gpus'):
      if 'nvidia.com/gpu' in limits:
        raise OrchestrateException(
          'The value in resources.gpus will override the value in resources.limits.nvidia.com/gpu,'
          'please remove one of these fields.'
        )
      limits['nvidia.com/gpu'] = resource_options.pop('gpus')

  def random_id_string(self):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(8))  # nosec

  def create_sigopt_experiment(self, optimization_options):
    data = optimization_options.copy()

    metadata = data.pop('metadata', None) or {}

    cluster = self.services.cluster_service.get_connected_cluster()
    metadata['cluster_name'] = cluster.name

    data["metadata"] = metadata

    experiment = self.services.sigopt_service.create_experiment(data)
    return experiment.id

  def create_controller(
    self,
    repository,
    tag,
    resource_options,
    run_command,
    controller_mode,
    controller_name,
    extra_labels,
    extra_env_vars,
  ):
    image_name = DockerService.format_image_name(repository, tag)
    cluster = self.services.cluster_service.get_connected_cluster()
    self.format_resources(resource_options)
    job_info_path = "/etc/job-info"
    job_info_volume_name = "job-info"
    env_vars = [
      {
        'name': 'KUBE_CONFIG',
        'value': "incluster",
      },
      {
        'name': 'USER_IMAGE',
        'value': image_name,
      },
      {
        'name': 'USER_RESOURCES',
        'value': json.dumps(resource_options),
      },
      {
        'name': 'NAMESPACE',
        'valueFrom': {
          'fieldRef': {
            'fieldPath': 'metadata.namespace',
          },
        },
      },
      {
        'name': "CLUSTER_NAME",
        'value': cluster.name,
      },
      {
        'name': 'JOB_INFO_PATH',
        'value': job_info_path,
      },
      {
        "name": "CONTROLLER_MODE",
        "value": controller_mode,
      },
      *(self.sigopt_env_vars()),
      *extra_env_vars,
    ]
    if self.services.sigopt_service.log_collection_enabled:
      env_vars.append({
        "name": "SIGOPT_LOG_COLLECTION_ENABLED",
        "value": "1",
      })

    labels = {
      "mode": controller_mode,
      "type": "controller",
      **extra_labels,
    }

    if not run_command:
      run_command = []

    controller_repo, controller_tag = DockerService.get_repository_and_tag(DEFAULT_CONTROLLER_IMAGE)
    controller_image_url = cluster.generate_image_tag(repository=controller_repo)
    controller_image_url += f":{controller_tag}"

    self.services.kubernetes_service.start_job({
      'apiVersion': 'batch/v1',
      'kind': 'Job',
      'metadata': {
        'name': controller_name,
        'labels': labels,
      },
      'spec': {
        'template': {
          'metadata': {
            'labels': labels,
          },
          'spec': {
            'serviceAccount': 'controller',
            'restartPolicy': 'Never',
            'containers': [
              {
                'image': controller_image_url,
                'imagePullPolicy': 'Always',
                'name': 'controller',
                'env': env_vars,
                'args': run_command,
                'volumeMounts': [
                  {
                    'name': job_info_volume_name,
                    'mountPath': job_info_path,
                  },
                ],
              },
            ],
            'volumes': [{
              # NOTE(taylor): the job-info downwardAPI volume allows the controller to link newly created pods
              # to the controller job so that the garbage collector will clean up dangling pods
              'name': job_info_volume_name,
              'downwardAPI': {
                'items': [
                  {
                    'path': 'name',
                    'fieldRef': {'fieldPath': "metadata.labels['job-name']"},
                  },
                  {
                    'path': 'uid',
                    'fieldRef': {'fieldPath': "metadata.labels['controller-uid']"},
                  },
                ],
              },
            }],
          },
        },
      },
    })

  def start_cluster_run(
    self,
    repository,
    tag,
    resource_options,
    run_command=None,
  ):
    self.services.kubernetes_service.check_nodes_are_ready()
    cluster = self.services.cluster_service.get_connected_cluster()

    random_string = self.random_id_string()
    run_name = "run-" + random_string
    run = self.services.sigopt_service.create_run(run_name, cluster)
    controller_name = f"run-controller-{random_string}"
    labels = {
      "run-name": run_name,
      "run": run.id,
    }
    env_vars = [
      {
        "name": "RUN_NAME",
        "value": run_name,
      },
      {
        "name": "RUN_ID",
        "value": run.id,
      },
    ]
    controller_mode = "run"

    self.create_controller(
      repository,
      tag,
      resource_options,
      run_command,
      controller_mode,
      controller_name,
      labels,
      env_vars,
    )

    return f"run/{run.id}"

  def start_cluster_experiment(
    self,
    repository,
    tag,
    optimization_options,
    resource_options,
    experiment_id=None,
    run_command=None,
  ):
    self.services.kubernetes_service.check_nodes_are_ready()

    experiment_id = experiment_id or self.create_sigopt_experiment(optimization_options)

    controller_name = f"experiment-controller-{experiment_id}"
    labels = {"experiment": str(experiment_id)}
    controller_mode = "experiment"
    env_vars = [{
      "name": self.EXPERIMENT_ENV_KEY,
      "value": str(experiment_id),
    }]

    self.create_controller(
      repository,
      tag,
      resource_options,
      run_command,
      controller_mode,
      controller_name,
      labels,
      env_vars,
    )

    return f"experiment/{experiment_id}"
