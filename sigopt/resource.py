# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from .endpoint import BoundApiEndpoint


_NO_ARG = object()


class BoundApiResource(object):
  def __init__(self, resource, id, path):
    self._resource = resource
    self._id = id

    self._base_path = list(path)
    if id is not _NO_ARG:
      self._base_path.append(id)

  def get_bound_entity(self, name):
    endpoint = self._resource._endpoints.get(name)
    if endpoint:
      return BoundApiEndpoint(self, endpoint)
    sub_resource = self._resource._sub_resources.get(name)
    if sub_resource:
      return PartiallyBoundApiResource(sub_resource, self)
    return None

  def __getattr__(self, attr):
    bound_entity = self.get_bound_entity(attr)
    if bound_entity:
      return bound_entity
    raise AttributeError(
      "Cannot find attribute `{attribute}` on resource `{resource}`, likely no"
      " endpoint exists for: {path}/{attribute}, or `{resource}` does not support"
      " `{attribute}`.".format(
        attribute=attr,
        resource=self._resource._name,
        path="/".join(self._base_path),
      )
    )


class PartiallyBoundApiResource(object):
  def __init__(self, resource, bound_parent_resource):
    self._resource = resource
    self._bound_parent_resource = bound_parent_resource

  def __call__(self, id=_NO_ARG):
    path = self._bound_parent_resource._base_path + [self._resource._name]
    return BoundApiResource(self._resource, id, path)


class BaseApiResource(object):
  def __init__(self, conn, name, endpoints=None, resources=None):
    self._conn = conn
    self._name = name

    self._endpoints = dict(((endpoint._attribute_name, endpoint) for endpoint in endpoints)) if endpoints else {}

    self._sub_resources = dict(((resource._name, resource) for resource in resources)) if resources else {}

  def __call__(self, id=_NO_ARG):
    return BoundApiResource(self, id, [self._name])


class ApiResource(BaseApiResource):
  def __init__(self, conn, name, endpoints=None, resources=None):
    super().__init__(
      conn=conn,
      name=name,
      endpoints=endpoints,
      resources=resources,
    )
