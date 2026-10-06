"""Image loading and simple averaging (box) filter smoothing."""

from pathlib import Path

import numpy as np
from PIL import Image

LUMA_WEIGHTS = np.array([0.299, 0.587, 0.114])


def load_image(path):
    """Load an image as a 2-D float64 grayscale array.

    * Single-band images are used as-is (8- or 16-bit values preserved).
    * RGB / RGBA images are converted with the ITU-R BT.601 luminance
      Y = 0.299 R + 0.587 G + 0.114 B.
    * Other multiband images (>3 bands, e.g. multispectral TIFF stacks) are
      reduced to the mean of their bands.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    try:
        img = Image.open(path)
        if img.mode in ("P", "PA", "LA", "1"):
            img = img.convert("RGBA" if "A" in img.mode else "L")
        arr = np.asarray(img).astype(np.float64)
    except Exception:
        # Float / multiband GeoTIFFs that Pillow cannot decode.
        if path.suffix.lower() not in (".tif", ".tiff"):
            raise
        import tifffile
        arr = np.asarray(tifffile.imread(path)).astype(np.float64)
        arr = np.squeeze(arr)
        if arr.ndim == 3 and arr.shape[0] < arr.shape[-1] and arr.shape[0] <= 16:
            arr = np.moveaxis(arr, 0, -1)  # band-first (C, H, W) -> (H, W, C)

    if arr.ndim == 2:
        return arr
    bands = arr.shape[2]
    if bands in (3, 4):
        return arr[..., :3] @ LUMA_WEIGHTS
    return arr.mean(axis=2)


def smooth_image(image, size):
    """Mean (box) filter: I_s(x, y) = (1 / N) * sum over the size x size window.

    Implemented manually with an integral image on a reflect-padded copy, so
    the output has the input's shape and every output pixel averages exactly
    N = size * size input pixels.
    """
    if size < 1 or size % 2 == 0:
        raise ValueError("Smoothing size must be a positive odd integer.")
    image = np.asarray(image, dtype=np.float64)
    H, W = image.shape
    half = size // 2
    padded = np.pad(image, half, mode="reflect")
    S = np.zeros((padded.shape[0] + 1, padded.shape[1] + 1))
    S[1:, 1:] = padded.cumsum(axis=0).cumsum(axis=1)
    total = (S[size:size + H, size:size + W]
             - S[0:H, size:size + W]
             - S[size:size + H, 0:W]
             + S[0:H, 0:W])
    return total / float(size * size)


def to_uint8(image, lo=None, hi=None):
    """Linearly scale an array to 0..255 for saving / display."""
    image = np.asarray(image, dtype=np.float64)
    lo = image.min() if lo is None else lo
    hi = image.max() if hi is None else hi
    if hi <= lo:
        return np.zeros(image.shape, dtype=np.uint8)
    return np.clip((image - lo) / (hi - lo) * 255.0, 0, 255).round().astype(np.uint8)


def high_frequency_energy(image):
    """Mean squared difference between neighbouring pixels (horizontal + vertical).

    Used to quantify how much fine detail smoothing removes.
    """
    image = np.asarray(image, dtype=np.float64)
    dx = np.diff(image, axis=1)
    dy = np.diff(image, axis=0)
    return float((np.mean(dx ** 2) + np.mean(dy ** 2)) / 2.0)
