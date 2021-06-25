from ..services.base import Service


RESOURCES_OPTION = 'resources_per_model'

class GpuOptionsValidatorService(Service):
  def get_resource_options(self, run_options):
    resource_options = run_options.get(RESOURCES_OPTION, {})
    gpus = resource_options.get('gpus')
    gpus = gpus and int(gpus)

    if gpus is not None:
      resource_options = resource_options.copy()
      resource_options['gpus'] = gpus
    return resource_options
