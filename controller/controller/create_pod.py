import os
import random
import string
from kubernetes import client as k8s_client

from sigopt.config import Config as SigOptConfig
from sigopt.run_context import GlobalRunContext


RUN_RANDOM_PART_LENGTH = 8
RUN_RANDOM_PART_CHARS = string.ascii_lowercase + string.digits

def get_run_pod_env_vars(run_context):
  config = SigOptConfig()
  config.set_context_entry(GlobalRunContext(run_context))
  env = [
    k8s_client.V1EnvVar(
      name="SIGOPT_API_TOKEN",
      value=os.environ["SIGOPT_API_TOKEN"],
    ),
    k8s_client.V1EnvVar(
      name="SIGOPT_API_URL",
      value=os.environ["SIGOPT_API_URL"],
    ),
    k8s_client.V1EnvVar(
      name="SIGOPT_PROJECT",
      value=os.environ["SIGOPT_PROJECT"],
    ),
    k8s_client.V1EnvVar(
      name="SIGOPT_RUN_ID",
      value=run_context.run.id,
    ),
    k8s_client.V1EnvVar(
      name="SIGOPT_RUN_NAME",
      value_from=k8s_client.V1EnvVarSource(
        field_ref=k8s_client.V1ObjectFieldSelector(
          field_path="metadata.name",
        ),
      ),
    ),
    *(
      k8s_client.V1EnvVar(
        name=key,
        value=value.decode("ascii"),
      ) for key, value in config.get_environment_context().items()
    ),
  ]
  return env

def random_run_name():
  return "run-" + "".join(random.choice(RUN_RANDOM_PART_CHARS) for _ in range(RUN_RANDOM_PART_LENGTH))

def create_run_pod(k8s_settings, run_context):
  run_id = run_context.id
  run_name = run_context.run.to_json()["name"]

  labels = {
    "run-name": run_name,
    "run": run_id,
  }
  env = get_run_pod_env_vars(run_context)
  node_topology_key = "kubernetes.io/hostname"
  # NOTE(taylor): preference to run on nodes with other runs
  pod_affinities = [
    k8s_client.V1WeightedPodAffinityTerm(
      weight=50,
      pod_affinity_term=k8s_client.V1PodAffinityTerm(
        label_selector=k8s_client.V1LabelSelector(
          match_labels={
            "type": "run",
          },
        ),
        topology_key=node_topology_key,
      ),
    ),
  ]
  volumes = []
  volume_mounts = []
  experiment_id = run_context.experiment
  if experiment_id:
    labels.update({"experiment": experiment_id})
    # NOTE(taylor): highest preference to run on nodes with runs in the same experiment
    pod_affinities.append(k8s_client.V1WeightedPodAffinityTerm(
      weight=100,
      pod_affinity_term=k8s_client.V1PodAffinityTerm(
        label_selector=k8s_client.V1LabelSelector(
          match_labels={
            "type": "run",
            "experiment": experiment_id,
          },
        ),
        topology_key=node_topology_key,
      ),
    ))

  unacceptable_node_group_types = ["system"]
  requests = k8s_settings.resources.get("requests") or {}
  limits = k8s_settings.resources.get("limits") or {}
  # NOTE(taylor): Preventing GPU-less jobs from running on GPU nodes forces the cluster autoscaler to scale up
  # CPU nodes. This prevents a situation where the GPU nodes are not scaled down because they are occupied by
  # CPU workloads. The cluster autoscaler does not know that it should create CPU nodes when the GPUs are unused.
  # TODO(taylor): This could cause unexpected behavior if the cluster has no CPU nodes. Running CPU jobs on GPU
  # nodes could also be an opportunity for more efficient resource utilization, but is avoided for now because the
  # workloads cannot be migrated onto CPU nodes by the cluster autoscaler as mentioned above.
  # NOTE(taylor): Applying a NoSchedule taint to GPU nodes is another way to achieve this behavior, but does not work as
  # well out of the box with clusters that orchestrate doesn't provision. Applying a PreferNoSchedule
  # taint to GPU nodes does not resolve the workload migration issue when there are no CPU nodes.
  if all(
    float(group.get("nvidia.com/gpu", 0)) == 0
    for group in (requests, limits)
  ):
    unacceptable_node_group_types.append("gpu")

  node_affinity = k8s_client.V1NodeAffinity(
    required_during_scheduling_ignored_during_execution=k8s_client.V1NodeSelector(
      node_selector_terms=[k8s_client.V1NodeSelectorTerm(
        match_expressions=[k8s_client.V1NodeSelectorRequirement(
          key="orchestrate.sigopt.com/node-group-type",
          operator="NotIn",
          values=unacceptable_node_group_types,
        )],
      )],
    ),
  )
  pod_affinity = k8s_client.V1PodAffinity(
    preferred_during_scheduling_ignored_during_execution=pod_affinities,
  )

  pod = k8s_client.V1Pod(
    metadata=k8s_client.V1ObjectMeta(
      owner_references=k8s_settings.owner_references,
      labels={
        "type": "run",
        **labels,
      },
      name=run_name,
    ),
    spec=k8s_client.V1PodSpec(
      affinity=k8s_client.V1Affinity(
        node_affinity=node_affinity,
        pod_affinity=pod_affinity,
      ),
      containers=[
        k8s_client.V1Container(
          name="model-runner",
          image=k8s_settings.image,
          resources=k8s_client.V1ResourceRequirements(**k8s_settings.resources),
          image_pull_policy="Always",
          command=[],
          args=k8s_settings.args,
          env=env,
          volume_mounts=volume_mounts,
          tty=True,
        ),
      ],
      volumes=volumes,
      restart_policy="Never",
    ),
  )
  k8s_settings.api.create_namespaced_pod(k8s_settings.namespace, pod)
  return pod
