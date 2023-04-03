# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
from enum import Enum

from ..exceptions import OrchestrateException


class Provider(Enum):
  AWS = 1
  CUSTOM = 2


STRING_TO_PROVIDER = dict(
  aws=Provider.AWS,
  custom=Provider.CUSTOM,
)
PROVIDER_TO_STRING = dict((v, k) for (k, v) in STRING_TO_PROVIDER.items())


class UnknownProviderStringError(OrchestrateException):
  def __init__(self, provider_string):
    if provider_string is None:
      provider_error = "Please include a provider with your request."
    else:
      provider_error = f"{provider_string!r} is not a supported provider."

    super().__init__(f"{provider_error} Supported providers are: {', '.join(STRING_TO_PROVIDER)}")
    self.provider_string = provider_string


def string_to_provider(provider_string):
  try:
    return STRING_TO_PROVIDER[provider_string.lower()]
  except (KeyError, AttributeError) as e:
    raise UnknownProviderStringError(provider_string) from e


def provider_to_string(provider):
  try:
    return PROVIDER_TO_STRING[provider]
  except KeyError as e:
    raise NotImplementedError() from e
