apiVersion: v1
clusters:
- cluster:
    server: "{{{endpoint_url}}}"
    certificate-authority-data: "{{{base64_encoded_ca_cert}}}"
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: orchestrate
  name: orchestrate
current-context: orchestrate
kind: Config
preferences: {}
users:
- name: orchestrate
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1alpha1
      command: {{{authenticator_binary_path}}}
      args:
        - "token"
        - "-i"
        - "{{{cluster_name}}}"
        {{{#role_arn}}}
        - "-r"
        - "{{{.}}}"
        {{{/role_arn}}}
