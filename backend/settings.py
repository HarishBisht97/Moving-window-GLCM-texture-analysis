import os
from pathlib import Path

from backend import PROJECT_ROOT

STORAGE_DIR = Path(os.environ.get("GLCM_STORAGE_DIR", PROJECT_ROOT / "storage"))
UPLOAD_DIR = STORAGE_DIR / "uploads"
ANALYSIS_DIR = STORAGE_DIR / "analyses"

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
MAX_IMAGE_SIDE = 4096

CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
