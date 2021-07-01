import copy
import pytest

from sigopt.validate.run_input import validate_run_input
from sigopt.validate.exceptions import ValidationError


VALID_RUN_INPUT = {
  "name": "test run",
  "run": "python test.py",
  "resources": {"gpus": 2},
}

class TestValidateRun:
  @pytest.mark.parametrize("mutator,expected_message", [
    (lambda r: r.__setitem__("name", ""), "name cannot be an empty string"),
    (lambda r: r.__setitem__("name", 1), "name must be a string"),
    (lambda r: r.__setitem__("name", {}), "name must be a string"),
    (lambda r: r.__setitem__("run", {}), "must be a command"),
    (lambda r: r.__setitem__("run", [1, 2, 3]), "has some non-string arguments"),
    (lambda r: r.__setitem__("resources", []), "must be a mapping"),
    (lambda r: r.__setitem__("resources", {1: 2}), "can only have string keys"),
  ])
  def test_invalid_run(self, mutator, expected_message):
    run_input = copy.deepcopy(VALID_RUN_INPUT)
    mutator(run_input)
    with pytest.raises(ValidationError) as validation_error:
      validate_run_input(run_input)
    assert expected_message in str(validation_error)

  @pytest.mark.parametrize("mutator,check", [
    (lambda r: r, lambda r: r["name"] == "test run"),
    (lambda r: r, lambda r: r["run"] == ["sh", "-c", "python test.py"]),
    (lambda r: r.__setitem__("run", ["python", "test.py"]), lambda r: r["run"] == ["python", "test.py"]),
    (lambda r: r.__delitem__("run"), lambda r: r["run"] == []),
    (lambda r: r.__setitem__("run", None), lambda r: r["run"] == []),
    (lambda r: r, lambda r: r["resources"] == {"gpus": 2}),
    (lambda r: r.__delitem__("resources"), lambda r: r["resources"] == {}),
  ])
  def test_valid_run(self, mutator, check):
    run_input = copy.deepcopy(VALID_RUN_INPUT)
    mutator(run_input)
    validated = validate_run_input(run_input)
    assert check(validated)
