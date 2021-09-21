import base64
import hashlib
import io
import mimetypes
import warnings

import png


def try_load_pil_image(image):
  try:
    from PIL.Image import Image as PILImage
  except ImportError:
    return None
  if isinstance(image, PILImage):
    image_data = io.BytesIO()
    image.save(image_data, "PNG")
    image_data.seek(0)
    return getattr(image, "filename", None), image_data, "image/png"
  return None

def try_load_matplotlib_image(image):
  try:
    from matplotlib.figure import Figure as MatplotlibFigure
  except ImportError:
    return None
  if isinstance(image, MatplotlibFigure):
    image_data = io.BytesIO()
    image.savefig(image_data, format="svg")
    image_data.seek(0)
    return None, image_data, "image/svg+xml"
  return None

def try_load_numpy_image(image):
  try:
    from numpy import ndarray, uint8 as numpy_uint8
  except ImportError:
    return None
  if isinstance(image, ndarray):
    channels = 0
    if len(image.shape) == 2:
      channels = 1
    elif len(image.shape) == 3:
      channels = image.shape[2]
    if not channels:
      raise Exception(f"images provided as numpy arrays must have 2 or 3 dimensions, provided shape: {image.shape}")
    channels_to_mode = {
      1: "L",
      3: "RGB",
      4: "RGBA",
    }
    if channels not in channels_to_mode:
      raise Exception(f"images provided as numpy arrays must have 1, 3 or 4 channels, provided channels: {channels}")
    mode = channels_to_mode[channels]
    clipped_image = image.clip(0, 255)
    byte_image = clipped_image.astype(numpy_uint8)
    height, width = image.shape[:2]
    pypng_compatible = byte_image.reshape(height, width * channels)
    writer = png.Writer(width, height, greyscale=(mode == "L"), alpha=(mode == "RGBA"))
    image_data = io.BytesIO()
    writer.write(image_data, pypng_compatible)
    return None, image_data, "image/png"
  return None


MIME_TYPE_REMAP = {
  # the mime type image/x-ms-bmp is returned in some environments
  # it is not officially supported by Chrome
  # it is still used in some cases for legacy IE7 support
  # prefer Chrome support over IE7 support
  "image/x-ms-bmp": "image/bmp",
}

SUPPORTED_IMAGE_MIME_TYPES = {
  "image/apng",
  "image/bmp",
  "image/gif",
  "image/jpeg",
  "image/png",
  "image/svg+xml",
  "image/webp",
  "image/x-icon",
}

def create_api_image_payload(image):
  if isinstance(image, str):
    content_type = mimetypes.guess_type(image)
    if content_type is None:
      warnings.warn(
        f"Could not guess image type from provided filename, skipping upload: {image}",
        RuntimeWarning,
      )
      return None
    content_type, _ = content_type
    content_type = MIME_TYPE_REMAP.get(content_type, content_type)
    if content_type not in SUPPORTED_IMAGE_MIME_TYPES:
      friendly_supported_types = ", ".join(sorted(SUPPORTED_IMAGE_MIME_TYPES))
      warnings.warn(
        f"File type `{content_type}` is not supported, please use one of the supported types:"
        f" {friendly_supported_types}",
        RuntimeWarning,
      )
      return None
    return image, open(image, "rb"), content_type
  payload = try_load_pil_image(image)
  if payload is not None:
    return payload
  payload = try_load_matplotlib_image(image)
  if payload is not None:
    return payload
  payload = try_load_numpy_image(image)
  if payload is not None:
    return payload
  warnings.warn(
    f"Image type not supported: {type(image)}."
    " Supported types: str, PIL.Image.Image, matplotlib.figure.Figure, numpy.ndarray",
    RuntimeWarning,
  )
  return None

def get_blob_properties(image_data):
  md5 = hashlib.md5()  # nosec
  image_data.seek(0)
  while True:
    chunk = image_data.read(2 ** 20)
    if not chunk:
      break
    md5.update(chunk)
  length = image_data.tell()
  b64_md5 = base64.b64encode(md5.digest()).decode()
  return length, b64_md5
