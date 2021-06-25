import socket
from urllib.parse import urlparse

import boto3
import certifi
import requests
from OpenSSL import SSL

from ..services.aws_base import AwsService


class AwsIamService(AwsService):
  def __init__(self, services, aws_services, **kwargs):
    super().__init__(services, aws_services)
    self._client = boto3.client('iam', **kwargs)
    self._iam = boto3.resource('iam', **kwargs)
    self._sts = boto3.client('sts', **kwargs)

  @property
  def client(self):
    return self._client

  @property
  def iam(self):
    return self._iam

  def get_user_arn(self):
    response = self.client.get_user()
    user = response['User']
    return user['Arn']

  def describe_eks_role(self, role_name):
    return self.iam.Role(role_name)

  def get_thumbprint_from_oidc_issuer(self, oidc_url):
    response = requests.get(f"{oidc_url}/.well-known/openid-configuration")
    response.raise_for_status()
    keys_url = response.json()["jwks_uri"]
    parsed_url = urlparse(keys_url)
    hostname = parsed_url.hostname
    port = parsed_url.port or 443
    context = SSL.Context(method=SSL.TLSv1_METHOD)
    context.load_verify_locations(cafile=certifi.where())
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
      ssl_conn = SSL.Connection(context, socket=sock)
      ssl_conn.connect((hostname, port))
      ssl_conn.setblocking(1)
      ssl_conn.do_handshake()
      ssl_conn.set_tlsext_host_name(hostname.encode())
      leaf_cert = ssl_conn.get_peer_cert_chain()[-1]
    sha1_fingerprint = leaf_cert.digest("sha1").decode("ascii")
    return "".join(c for c in sha1_fingerprint if c != ":")

  def ensure_eks_oidc_provider(self, eks_cluster):
    url = eks_cluster["cluster"]["identity"]["oidc"]["issuer"]
    client_ids = ["sts.amazonaws.com"]
    thumbprint = self.get_thumbprint_from_oidc_issuer(url)
    try:
      self.client.create_open_id_connect_provider(
        Url=url,
        ClientIDList=client_ids,
        ThumbprintList=[thumbprint],
      )
    except self.client.exceptions.EntityAlreadyExistsException:
      pass

  def get_oidc_arn(self, url):
    _, provider = url.split("https://")
    account_id = self._sts.get_caller_identity()["Account"]
    return f"arn:aws:iam::{account_id}:oidc-provider/{provider}"

  def ensure_eks_oidc_provider_deleted(self, eks_cluster):
    url = eks_cluster["cluster"]["identity"]["oidc"]["issuer"]
    arn = self.get_oidc_arn(url)
    try:
      self.client.delete_open_id_connect_provider(OpenIDConnectProviderArn=arn)
    except self.client.exceptions.NoSuchEntityException:
      pass

  def _role_name_from_role_arn(self, role_arn):
    return role_arn.split(':role/')[1]

  def attach_policy(self, role_arn, policy_arn):
    role_name = self._role_name_from_role_arn(role_arn)
    self.iam.Role(role_name).attach_policy(PolicyArn=policy_arn)

  def get_cluster_access_role_arn(self, cluster_name):
    role_name = f"{cluster_name}-k8s-access-role"
    return self.iam.Role(role_name).arn

  def get_role_from_arn(self, role_arn):
    role_name = self._role_name_from_role_arn(role_arn)
    role = self.iam.Role(role_name)
    assert role.arn == role_arn
    return role
