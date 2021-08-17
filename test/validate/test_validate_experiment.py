import copy
import pytest

from sigopt.validate.experiment_input import validate_experiment_input
from sigopt.validate.exceptions import ValidationError


VALID_EXPERIMENT_INPUT = {
  "name": "test experiment",
  "parameters": [
    {
      "name": "p1",
      "type": "int",
      "bounds": {
        "min": 0,
        "max": 1,
      },
    },
  ],
  "metrics": [{"name": "m1"}],
  "budget": 10,
  "parallel_bandwidth": 4,
}

class TestValidateExperiment:
  @pytest.mark.parametrize("mutator,expected_message", [
    (lambda e: e.__delitem__("name"), "name is required"),
    (lambda e: e.__setitem__("name", None), "name must be a string"),
    (lambda e: e.__setitem__("name", ""), "name cannot be an empty string"),
    (lambda e: e.__setitem__("name", 1), "name must be a string"),
    (lambda e: e.__setitem__("name", {}), "name must be a string"),
    (lambda e: e.__delitem__("parameters"), "parameters is required"),
    (lambda e: e.__setitem__("parameters", None), "parameters must be a non-empty list"),
    (lambda e: e.__setitem__("parameters", {}), "parameters must be a non-empty list"),
    (lambda e: e.__setitem__("parameters", []), "parameters must be a non-empty list"),
    (lambda e: e["parameters"].__setitem__(0, []), "parameters must be a mapping"),
    (lambda e: e["parameters"][0].__delitem__("name"), "parameters require a name"),
    (lambda e: e["parameters"][0].__setitem__("name", None), "parameter name must be a string"),
    (lambda e: e["parameters"][0].__setitem__("name", ""), "parameter name cannot be an empty string"),
    (lambda e: e["parameters"][0].__delitem__("type"), "parameters require a type"),
    (lambda e: e["parameters"][0].__setitem__("type", None), "parameter type must be a string"),
    (lambda e: e["parameters"][0].__setitem__("type", {}), "parameter type must be a string"),
    (lambda e: e["parameters"][0].__setitem__("type", ""), "parameter type cannot be an empty string"),
    (lambda e: e.__delitem__("metrics"), "metrics is required"),
    (lambda e: e.__setitem__("metrics", None), "metrics must be a non-empty list"),
    (lambda e: e.__setitem__("metrics", {}), "metrics must be a non-empty list"),
    (lambda e: e.__setitem__("metrics", []), "metrics must be a non-empty list"),
    (lambda e: e["metrics"].__setitem__(0, []), "metrics must be a mapping"),
    (lambda e: e["metrics"][0].__delitem__("name"), "metrics require a name"),
    (lambda e: e["metrics"][0].__setitem__("name", None), "metric name must be a string"),
    (lambda e: e["metrics"][0].__setitem__("name", ""), "metric name cannot be an empty string"),
    (lambda e: e.__setitem__("budget", []), "budget must be a non-negative number"),
    (lambda e: e.__setitem__("budget", -1), "budget must be a non-negative number"),
    (lambda e: e.__setitem__("budget", float("inf")), "budget cannot be infinity"),
    (lambda e: e.__setitem__("parallel_bandwidth", []), "parallel_bandwidth must be a positive integer"),
    (lambda e: e.__setitem__("parallel_bandwidth", -1), "parallel_bandwidth must be a positive integer"),
    (lambda e: e.__setitem__("parallel_bandwidth", 0), "parallel_bandwidth must be a positive integer"),
    (lambda e: e.__setitem__("parallel_bandwidth", 0.5), "parallel_bandwidth must be a positive integer"),
  ])
  def test_invalid_experiment(self, mutator, expected_message):
    experiment_input = copy.deepcopy(VALID_EXPERIMENT_INPUT)
    mutator(experiment_input)
    with pytest.raises(ValidationError) as validation_error:
      validate_experiment_input(experiment_input)
    assert expected_message in str(validation_error)

  @pytest.mark.parametrize("mutator,check", [
    (lambda e: e, lambda e: e["name"] == "test experiment"),
    (lambda e: e, lambda e: e["parameters"] == [{"name": "p1", "type": "int", "bounds": {"min": 0, "max": 1}}]),
    (lambda e: e, lambda e: e["metrics"] == [{"name": "m1"}]),
    (lambda e: e, lambda e: e["parallel_bandwidth"] == 4),
    # support new features without needing to write new validation
    (lambda e: e.__setitem__("unrecognized_key", []), lambda e: e["unrecognized_key"] == []),
    (lambda e: e["parameters"][0].__setitem__("unrecognized_key", []), lambda e: e["parameters"][0]["unrecognized_key"] == []),
    (lambda e: e["metrics"][0].__setitem__("unrecognized_key", []), lambda e: e["metrics"][0]["unrecognized_key"] == []),
  ])
  def test_valid_experiment(self, mutator, check):
    experiment_input = copy.deepcopy(VALID_EXPERIMENT_INPUT)
    mutator(experiment_input)
    validated = validate_experiment_input(experiment_input)
    assert check(validated)
