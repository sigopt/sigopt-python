import json
import os
import sys

import kubernetes
import kubernetes.client as k8s_client
import sigopt


class SigOptSettings:
  def __init__(self):
    self.project = os.environ["SIGOPT_PROJECT"]
    self.client = os.environ["SIGOPT_CLIENT"]
    self.api_token = os.environ["SIGOPT_API_TOKEN"]
    self.api_url = os.environ["SIGOPT_API_URL"]
    self.log_collection_enabled = bool(os.environ.get("SIGOPT_LOG_COLLECTION_ENABLED"))
    self.conn = sigopt.Connection(self.api_token)
    self.conn.set_api_url(self.api_url)

class K8sSettings:
  def __init__(self):
    if os.environ.get("KUBE_CONFIG") == "incluster":
      kubernetes.config.load_incluster_config()
    else:
      kubernetes.config.load_kube_config()
    self.api = kubernetes.client.CoreV1Api()
    self.namespace = os.environ["NAMESPACE"]
    self.image = os.environ["USER_IMAGE"]
    self.args = sys.argv[1:]
    self.cluster_name = os.environ["CLUSTER_NAME"]
    self.resources = json.loads(os.environ.get("USER_RESOURCES", "{}"))
    self.job_info_path = os.environ["JOB_INFO_PATH"]
    job_info = []
    for info_key in "name", "uid":
      with open(os.path.join(self.job_info_path, info_key)) as job_info_fp:
        job_info.append(job_info_fp.read())
    self.job_name, self.job_uid = job_info
    self.owner_references = [k8s_client.V1OwnerReference(
      name=self.job_name,
      api_version="batch/v1",
      controller=True,
      uid=self.job_uid,
      kind="job",
      block_owner_deletion=True,
    )]

class BaseSettings:
  def __init__(self):
    self.sigopt_settings = SigOptSettings()
    self.k8s_settings = K8sSettings()

class ExperimentSettings(BaseSettings):
  def __init__(self):
    super().__init__()
    self.experiment_id = os.environ["ORCHESTRATE_EXPERIMENT_ID"]

class RunSettings(BaseSettings):
  def __init__(self):
    super().__init__()
    self.run_name = os.environ["RUN_NAME"]
    self.run_id = os.environ["RUN_ID"]
