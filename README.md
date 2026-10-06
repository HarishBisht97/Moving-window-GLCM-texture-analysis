# GLCM Texture Analyzer

Moving-window GLCM texture analysis (ASM, Contrast, Mean) with K-Means clustering, applied to an
image and its 7x7 / 9x9 averaged versions.

- `src/` – the image-processing pipeline (GLCM, features, smoothing, K-Means, statistics, figures)
- `backend/` – FastAPI layer that runs the `src/` pipeline as background jobs
- `frontend/` – React + TypeScript + Vite + Tailwind web interface
- `GLCM_Texture_KMeans.ipynb` – notebook report

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd frontend && npm install
```

## Run the web app

In two terminals, from the project root:

```bash
.venv/bin/uvicorn backend.app:app --reload --port 8000
```

```bash
cd frontend && npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` to the backend on port 8000.
Uploaded images and analysis outputs are stored in `storage/` (override with `GLCM_STORAGE_DIR`).

## Command line and tests

```bash
.venv/bin/python src/main.py --image data/aerial_sample.png --window 7 --levels 8 --k 4
.venv/bin/python -m pytest tests
```
