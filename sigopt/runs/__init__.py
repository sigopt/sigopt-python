from ..config import config
from .factory import RunFactory, ExperimentFactory
from .proxy import ProxyMethod


class RunContextProxyMethod(ProxyMethod):
  @property
  def instance(self):
    return RunFactory.get_global_run_context()

class RunFactoryProxyMethod(ProxyMethod):
  instance = RunFactory.from_config(config)

class ExperimentFactoryProxyMethod(ProxyMethod):
  instance = ExperimentFactory()

set_parameters= RunContextProxyMethod('set_parameters')
get_parameter = RunContextProxyMethod('get_parameter')
log_checkpoint = RunContextProxyMethod('log_checkpoint')
log_dataset = RunContextProxyMethod('log_dataset')
log_metadata = RunContextProxyMethod('log_metadata')
log_metric = RunContextProxyMethod('log_metric')
log_model = RunContextProxyMethod('log_model')
log_failure = RunContextProxyMethod('log_failure')
log_source_code = RunContextProxyMethod('log_source_code')
log_image = RunContextProxyMethod('log_image')

create_run = RunFactoryProxyMethod('create_run')
create_global_run = RunFactoryProxyMethod('create_global_run')
create_experiment = ExperimentFactoryProxyMethod('create_experiment')
