apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapRoles: |
    - rolearn: "{{node_instance_role_arn}}"
      username: {{=<% %>=}}system:node:{{EC2PrivateDNSName}}<%={{ }}=%>
      groups:
        - system:bootstrappers
        - system:nodes
  {{#cluster_access_role_arn}}
    - rolearn: "{{cluster_access_role_arn}}"
      username: "{{cluster_access_role_name}}"
      groups:
        - system:masters
  {{/cluster_access_role_arn}}
