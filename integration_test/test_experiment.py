import sigopt


class TestExperiment(object):
  def test_update(self):
    parameters = [
      {
        'name': 'max_depth',
        'type': 'int',
        'bounds': {'min': 2, 'max': 5}
      },
      {
        'name': 'num_boost_round',
        'type': 'int',
        'bounds': {'min': 2, 'max': 5}
      },
    ]
    config = {
      'name': 'experiment-integration-test',
      'type': 'offline',
      'parameters': parameters,
      'metrics': [{
        'name': 'f1',
        'strategy': 'optimize',
        'objective': 'maximize'
      }],
      'parallel_bandwidth': 1,
      'budget': 3
    }
    experiment = sigopt.create_aiexperiment(**config)
    parameters = experiment.parameters
    parameters[0].bounds.max = 100
    parameters[1].bounds.min = 1
    new_config = {
      'name': 'experiment-integration-test-1',
      'parameters': parameters,
      'parallel_bandwidth': 2,
      'budget': 4
    }
    experiment.update(**new_config)
    updated_experiment = sigopt.get_experiment(experiment.id)
    assert updated_experiment.name == 'experiment-integration-test-1'
    assert updated_experiment.budget == 4
    assert updated_experiment.parallel_bandwidth == 2
    assert updated_experiment.parameters[0].bounds.min == 2
    assert updated_experiment.parameters[0].bounds.max == 100
    assert updated_experiment.parameters[1].bounds.min == 1
    assert updated_experiment.parameters[1].bounds.max == 5
