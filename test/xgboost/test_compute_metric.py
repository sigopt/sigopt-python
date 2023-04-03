# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import numpy
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error, mean_squared_error

from sigopt.xgboost.compute_metrics import (
  compute_accuracy,
  compute_classification_report,
  compute_mae,
  compute_mse,
  compute_positives_and_negatives,
)


def verify_classification_metrics_against_sklearn(y_true, y_pred):
  report_compute = compute_classification_report(y_true, y_pred)
  report_sklearn = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
  assert numpy.isclose(
    report_compute["weighted avg"]["precision"],
    report_sklearn["weighted avg"]["precision"],
  )
  assert numpy.isclose(report_compute["weighted avg"]["recall"], report_sklearn["weighted avg"]["recall"])
  assert numpy.isclose(
    report_compute["weighted avg"]["f1-score"],
    report_sklearn["weighted avg"]["f1-score"],
  )
  assert numpy.abs(compute_accuracy(y_true, y_pred) - accuracy_score(y_true, y_pred)) < 1e-8
  classes = numpy.unique(y_true)
  for c in classes:
    label = str(c)
    assert numpy.isclose(report_compute[label]["precision"], report_sklearn[label]["precision"])
    assert numpy.isclose(report_compute[label]["recall"], report_sklearn[label]["recall"])
    assert numpy.isclose(report_compute[label]["f1-score"], report_sklearn[label]["f1-score"])


class TestComputeMetrics(object):
  def test_compute_positives_and_negatives(self):
    y_true = numpy.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
    y_pred = numpy.array([1, 0, 0, 0, 0, 0, 0, 1, 0, 0])
    tp, tn, fp, fn = compute_positives_and_negatives(y_true, y_pred, 1)
    assert sum([tp, tn, fp, fn]) == len(y_true)
    assert tp == 1
    assert tn == 6
    assert fp == 1
    assert fn == 2

    y_true = numpy.array([1, 1, 1, 2, 2, 2, 0, 0, 0, 0])
    y_pred = numpy.array([1, 0, 0, 0, 0, 0, 1, 1, 0, 0])
    tp, tn, fp, fn = compute_positives_and_negatives(y_true, y_pred, 2)
    assert sum([tp, tn, fp, fn]) == len(y_true)
    assert tp == 0
    assert tn == 7
    assert fp == 0
    assert fn == 3

  def test_binary_classification_one_true_label(self):
    y_true = numpy.zeros(10, dtype=int)
    y_pred = numpy.ones(10, dtype=int)
    assert compute_accuracy(y_true, y_pred) == 0
    report = compute_classification_report(y_true, y_pred)
    assert "1" not in report.keys()
    assert report["0"]["precision"] == 0
    assert report["0"]["recall"] == 0
    assert report["0"]["f1-score"] == 0
    assert report["weighted avg"]["precision"] == 0
    assert report["weighted avg"]["recall"] == 0
    assert report["weighted avg"]["f1-score"] == 0

  def test_binary_classification_one_pred_label(self):
    y_true = numpy.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
    y_pred = numpy.ones(10, dtype=int)
    assert compute_accuracy(y_true, y_pred) == 0.3
    report = compute_classification_report(y_true, y_pred)
    assert report["0"]["precision"] == 0
    assert report["0"]["recall"] == 0
    assert report["0"]["f1-score"] == 0
    assert report["1"]["precision"] == 0.3
    assert report["1"]["recall"] == 1.0
    assert numpy.isclose(report["1"]["f1-score"], 2 * (1.0 * 0.3) / (1.0 + 0.3))
    assert report["weighted avg"]["precision"] == 0.3 * 0.3
    assert report["weighted avg"]["recall"] == 0.3
    assert numpy.isclose(report["weighted avg"]["f1-score"], 2 * (1.0 * 0.3) / (1.0 + 0.3) * 0.3)

  def test_binary_classification_against_sklearn(self):
    n_samples = 30
    y_true = numpy.random.randint(2, size=n_samples)
    y_pred = numpy.random.randint(2, size=n_samples)
    verify_classification_metrics_against_sklearn(y_true, y_pred)

  def test_multiclass_classification_metrics(self):
    n_samples = 50
    y_true = numpy.random.randint(3, size=n_samples)
    y_pred = numpy.random.randint(2, size=n_samples)
    verify_classification_metrics_against_sklearn(y_true, y_pred)

    y_pred = numpy.random.randint(3, size=n_samples)
    verify_classification_metrics_against_sklearn(y_true, y_pred)

  def test_regression_metrics(self):
    # Check regression metrics
    n_samples = 10
    y_true = 2 * numpy.ones(n_samples)
    assert numpy.isclose(compute_mae(y_true, numpy.zeros(n_samples)), 2.0)
    assert numpy.isclose(compute_mse(y_true, numpy.zeros(n_samples)), 4.0)

    y_true = numpy.random.randn(n_samples)
    assert numpy.isclose(compute_mae(y_true, y_true), 0)
    assert numpy.isclose(compute_mse(y_true, y_true), 0)

    y_pred = numpy.random.randn(n_samples)
    # pylint: disable=arguments-out-of-order
    assert numpy.isclose(compute_mae(y_true, y_pred), compute_mae(y_pred, y_true))
    assert numpy.isclose(compute_mse(y_true, y_pred), compute_mse(y_pred, y_true))
    # pylint: enable=arguments-out-of-order
    assert numpy.isclose(compute_mae(y_true, y_pred), numpy.sum(numpy.abs(y_true - y_pred)) / n_samples)
    assert numpy.isclose(compute_mse(y_true, y_pred), numpy.sum((y_true - y_pred) ** 2) / n_samples)

    assert numpy.isclose(compute_mae(y_true, y_pred), mean_absolute_error(y_true, y_pred))
    assert numpy.isclose(compute_mse(y_true, y_pred), mean_squared_error(y_true, y_pred))
