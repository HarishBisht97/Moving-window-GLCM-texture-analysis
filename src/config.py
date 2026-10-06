"""Global configuration for the moving-window GLCM texture experiment.

Every experiment (original, 7x7 smoothed, 9x9 smoothed) uses exactly these
parameters so that the results are directly comparable.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DEFAULT_IMAGE = DATA_DIR / "aerial_sample.png"

GLCM_WINDOW_SIZE = 7      # side length of the moving window (odd)
GRAY_LEVELS = 8           # number of quantized gray levels L
DISTANCE = 1              # pixel distance d of the co-occurrence pair
ANGLE = 0                 # direction in degrees: 0, 45, 90 or 135
SYMMETRIC = False         # count (i, j) and (j, i) together if True
NUM_CLUSTERS = 4          # K for K-Means
RANDOM_STATE = 0          # fixed seed for reproducible K-Means
KMEANS_N_INIT = 10

SMOOTHING_SIZES = [7, 9]  # averaging-filter sizes for the smoothing cases

FEATURE_NAMES = ["ASM", "CON", "MEAN"]
