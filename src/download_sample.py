"""Download a public-domain aerial image into data/.

Primary source: USC-SIPI Image Database, "Aerials" volume (512x512 8-bit
grayscale aerial photographs). If that fails, a few alternative public URLs
are tried (a public-domain 1946 aerial photograph on Wikimedia Commons). The
image is converted to grayscale, centre-cropped to 512x512 at native
resolution and saved as an 8-bit PNG at ``config.DEFAULT_IMAGE``.

Usage:
    python src/download_sample.py [--force]
"""

import argparse
import io
import sys
import urllib.request

import numpy as np
from PIL import Image

import config

SOURCES = [
    ("USC-SIPI aerial 2.1.01",
     "https://sipi.usc.edu/database/download.php?vol=aerials&img=2.1.01"),
    ("USC-SIPI aerial 2.1.02",
     "https://sipi.usc.edu/database/download.php?vol=aerials&img=2.1.02"),
    ("USC-SIPI aerial 2.2.01",
     "https://sipi.usc.edu/database/download.php?vol=aerials&img=2.2.01"),
    ("Wikimedia Commons (public domain): State Library of Queensland, "
     "aerial photograph of the Darling Downs district showing rivers and farmlands, 1946",
     "https://upload.wikimedia.org/wikipedia/commons/3/3b/StateLibQld_2_117380_"
     "Aerial_photograph_of_the_Darling_Downs_district_showing_rivers_and_farmlands%2C_1946.jpg"),
]

USER_AGENT = "Mozilla/5.0 (GNR607 GLCM texture project)"
MAX_SIDE = 512


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def to_grayscale_png(raw_bytes, out_path):
    img = Image.open(io.BytesIO(raw_bytes))
    img = img.convert("L")
    w, h = img.size
    if min(w, h) >= MAX_SIDE:
        # Centre crop keeps the native resolution, so fine texture is preserved.
        left, top = (w - MAX_SIDE) // 2, (h - MAX_SIDE) // 2
        img = img.crop((left, top, left + MAX_SIDE, top + MAX_SIDE))
    elif max(w, h) > MAX_SIDE:
        img.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return np.asarray(img)


def download_sample(out_path=config.DEFAULT_IMAGE, force=False):
    if out_path.exists() and not force:
        print(f"Sample already present: {out_path}")
        return out_path
    for name, url in SOURCES:
        try:
            print(f"Trying {name} ...")
            arr = to_grayscale_png(fetch(url), out_path)
            print(f"Saved {out_path} ({arr.shape[1]}x{arr.shape[0]}) from {name}")
            (out_path.parent / "SOURCE.txt").write_text(f"{name}\n{url}\n")
            return out_path
        except Exception as exc:  # network / decode errors: try next source
            print(f"  failed: {exc}")
    raise RuntimeError("Could not download any sample image; place one in data/ manually.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="re-download even if present")
    args = parser.parse_args()
    try:
        download_sample(force=args.force)
    except RuntimeError as err:
        print(err)
        sys.exit(1)
