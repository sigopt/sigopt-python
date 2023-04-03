# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import matplotlib
import pytest


matplotlib.use("Agg")

import io
import os
import xml.etree.ElementTree as ET

import numpy
from matplotlib import pyplot as plt
from PIL import Image
from utils import ObserveWarnings

from sigopt.file_utils import (
  create_api_image_payload,
  get_blob_properties,
  try_load_matplotlib_image,
  try_load_numpy_image,
  try_load_pil_image,
)


@pytest.fixture
def pil_image():
  return Image.new("RGB", (16, 16), (255, 0, 0))


@pytest.fixture
def matplotlib_figure():
  figure = plt.figure()
  plt.plot([1, 2, 3, 4])
  plt.ylabel("for testing")
  return figure


def test_load_pil_image(pil_image):
  data = try_load_pil_image(pil_image)

  assert data is not None

  filename, image_data, content_type = data
  assert filename is None

  with Image.open(image_data) as loaded_image:
    assert numpy.all(numpy.array(loaded_image) == numpy.array(pil_image))

  assert content_type == "image/png"


def test_load_matplotlib_image(matplotlib_figure):
  data = try_load_matplotlib_image(matplotlib_figure)

  assert data is not None

  filename, image_data, content_type = data
  assert filename is None

  image_data.seek(0)
  contents = image_data.read()
  assert b"for testing" in contents

  # check that the svg is at least valid xml
  ET.fromstring(contents)

  assert content_type == "image/svg+xml"


def test_load_HxW_numpy_image():
  numpy_img = numpy.random.randint(0, 255, (32, 16))
  data = try_load_numpy_image(numpy_img)

  assert data is not None

  filename, image_data, content_type = data
  assert filename is None

  image_data.seek(0)
  with Image.open(image_data) as pil_image:
    loaded_numpy_img = numpy.array(pil_image)

  assert loaded_numpy_img.shape[:2] == (32, 16)

  assert numpy.all(numpy_img == loaded_numpy_img)

  assert content_type == "image/png"


@pytest.mark.parametrize("N", [1, 3, 4])
def test_load_HxWxN_numpy_image(N):
  numpy_img = numpy.random.randint(0, 255, (32, 16, N))
  data = try_load_numpy_image(numpy_img)

  assert data is not None

  filename, image_data, content_type = data
  assert filename is None

  image_data.seek(0)
  with Image.open(image_data) as pil_image:
    loaded_numpy_img = numpy.array(pil_image)

  assert loaded_numpy_img.shape[:2] == (32, 16)
  loaded_numpy_img = loaded_numpy_img.reshape((32, 16, N))

  assert numpy.all(numpy_img == loaded_numpy_img)

  assert content_type == "image/png"


def test_load_numpy_image_clipping():
  numpy_img = numpy.ones((32, 16)) * 512
  numpy_img[:16] = -256
  data = try_load_numpy_image(numpy_img)

  assert data is not None

  filename, image_data, content_type = data
  assert filename is None

  image_data.seek(0)
  with Image.open(image_data) as pil_image:
    loaded_numpy_img = numpy.array(pil_image)

  assert loaded_numpy_img.shape[:2] == (32, 16)

  assert numpy.all(loaded_numpy_img[:16] == 0)
  assert numpy.all(loaded_numpy_img[16:] == 255)

  assert content_type == "image/png"


@pytest.mark.parametrize(
  "image_path,expected_type",
  [
    ("test.png", "image/png"),
    ("test.svg", "image/svg+xml"),
    ("test.bmp", "image/bmp"),
  ],
)
def test_create_api_image_payload_string_path(image_path, expected_type):
  image_path = os.path.join("./test/runs/test_files", image_path)
  data = create_api_image_payload(image_path)
  assert data is not None
  filepath, image_data, content_type = data
  with image_data:
    image_data.seek(0)
    with open(image_path, "rb") as fp:
      original_contents = fp.read()
    assert image_data.read() == original_contents
  assert filepath == image_path
  assert content_type == expected_type


def test_create_api_image_payload_string_path_bad_type():
  with ObserveWarnings() as w:
    path = "./test/runs/test_files/test.txt"
    data = create_api_image_payload(path)
    assert data is None
    assert len(w) == 1
    assert issubclass(w[-1].category, RuntimeWarning)


def test_create_api_image_payload_pil_image(pil_image):
  data = create_api_image_payload(pil_image)
  assert data is not None
  filepath, _, content_type = data
  assert filepath is None
  assert content_type == "image/png"


def test_create_api_image_payload_matplotlib_figure(matplotlib_figure):
  data = create_api_image_payload(matplotlib_figure)
  assert data is not None
  filepath, _, content_type = data
  assert filepath is None
  assert content_type == "image/svg+xml"


def test_create_api_image_payload_numpy_image():
  numpy_image = numpy.random.randint(0, 255, (16, 16))
  data = create_api_image_payload(numpy_image)
  assert data is not None
  filepath, _, content_type = data
  assert filepath is None
  assert content_type == "image/png"


def test_create_api_image_payload_unsupported_type():
  with ObserveWarnings() as w:
    data = create_api_image_payload({})
    assert data is None
    assert len(w) >= 1
    assert issubclass(w[-1].category, RuntimeWarning)


def test_get_blob_properties():
  data = "some\nblob\ndata\n".encode()
  blob = io.BytesIO(data)
  expected_b64_md5 = "hlXKMpBfPY7uZV7oFfHr2w=="
  length, b64_md5 = get_blob_properties(blob)
  assert length == len(data)
  assert b64_md5 == expected_b64_md5
