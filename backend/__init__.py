"""FastAPI layer around the existing GLCM texture pipeline in ``src/``."""

import sys
from pathlib import Path

import matplotlib

# Figures are rendered in a worker thread without a display.
matplotlib.use("Agg")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
