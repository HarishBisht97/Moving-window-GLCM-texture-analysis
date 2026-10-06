"""FastAPI application exposing the existing GLCM texture pipeline.

Run from the project root:
    .venv/bin/uvicorn backend.app:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from backend import settings
from backend.routes import analysis, images

settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="GLCM Texture Analyzer API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(images.router)
app.include_router(analysis.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/config")
def defaults():
    """Default parameters and fixed settings of the existing pipeline."""
    return {
        "glcmWindowSize": config.GLCM_WINDOW_SIZE, "grayLevels": config.GRAY_LEVELS,
        "distance": config.DISTANCE, "angle": config.ANGLE, "clusters": config.NUM_CLUSTERS,
        "randomState": config.RANDOM_STATE, "smoothingSizes": list(config.SMOOTHING_SIZES),
        "allowedExtensions": sorted(settings.ALLOWED_EXTENSIONS),
    }
