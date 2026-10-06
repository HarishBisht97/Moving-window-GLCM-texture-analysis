"""Uploaded image storage and metadata. Loading uses the existing ``load_image``."""

import json
import re
import uuid
from pathlib import Path

import numpy as np
from PIL import Image

from backend import settings
from backend.schemas.analysis import ImageMetadata
from preprocess import load_image, to_uint8
from visualize import gray_range

_ID_RE = re.compile(r"^[0-9a-f]{32}$")
PIL_MODE_DTYPES = {"1": "bool", "L": "uint8", "P": "uint8", "LA": "uint8", "RGB": "uint8",
                   "RGBA": "uint8", "CMYK": "uint8", "I;16": "uint16", "I;16B": "uint16",
                   "I;16L": "uint16", "I": "int32", "F": "float32"}


class ImageError(ValueError):
    pass


def valid_id(value):
    return bool(_ID_RE.match(value or ""))


def image_dir(image_id):
    if not valid_id(image_id):
        raise ImageError("Invalid image id")
    return settings.UPLOAD_DIR / image_id


def _source_dtype(path):
    """(dtype string, band count) of the file as stored on disk."""
    try:
        with Image.open(path) as im:
            return PIL_MODE_DTYPES.get(im.mode, im.mode), len(im.getbands())
    except Exception:
        import tifffile
        with tifffile.TiffFile(path) as tf:
            page = tf.series[0]
            shape = [s for s in page.shape if s > 1]
            bands = 1 if len(shape) <= 2 else min(shape)
            return str(page.dtype), bands


def save_upload(filename, data):
    """Store the uploaded bytes, load them with ``load_image`` and write a preview."""
    suffix = Path(filename or "").suffix.lower()
    if suffix not in settings.ALLOWED_EXTENSIONS:
        raise ImageError(f"Unsupported file type '{suffix}'. Allowed: "
                         + ", ".join(sorted(settings.ALLOWED_EXTENSIONS)))
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise ImageError("File is too large")

    image_id = uuid.uuid4().hex
    folder = settings.UPLOAD_DIR / image_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"source{suffix}"
    path.write_bytes(data)

    try:
        image = load_image(path)
        dtype, bands = _source_dtype(path)
    except Exception as exc:
        raise ImageError(f"Could not read image: {exc}") from exc
    if image.ndim != 2:
        raise ImageError("Image could not be converted to a single grayscale band")
    h, w = image.shape
    if min(h, w) < 16:
        raise ImageError("Image is too small (minimum 16 x 16 pixels)")
    if max(h, w) > settings.MAX_IMAGE_SIDE:
        raise ImageError(f"Image is too large (maximum {settings.MAX_IMAGE_SIDE} px per side)")

    Image.fromarray(to_uint8(image, *gray_range(image))).save(folder / "preview.png")
    meta = ImageMetadata(
        image_id=image_id, filename=Path(filename).name,
        preview_url=f"/api/images/{image_id}/preview",
        width=w, height=h, data_type=dtype, bands=bands,
        min=float(image.min()), max=float(image.max()),
        mean=float(image.mean()), std=float(image.std()),
    )
    (folder / "meta.json").write_text(meta.model_dump_json(by_alias=True))
    return meta


def get_metadata(image_id):
    path = image_dir(image_id) / "meta.json"
    if not path.exists():
        raise ImageError("Image not found")
    return ImageMetadata.model_validate(json.loads(path.read_text()))


def source_path(image_id):
    folder = image_dir(image_id)
    for p in folder.glob("source.*"):
        return p
    raise ImageError("Image not found")


def preview_path(image_id):
    path = image_dir(image_id) / "preview.png"
    if not path.exists():
        raise ImageError("Image not found")
    return path


def load_source(image_id):
    return np.asarray(load_image(source_path(image_id)))
