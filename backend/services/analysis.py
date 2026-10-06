"""Background analysis jobs that call the existing ``run_experiment`` pipeline."""

import io
import json
import re
import threading
import time
import traceback
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import config
from backend import settings
from backend.schemas.analysis import (AnalysisParameters, AnalysisResult, ClusterStatistics,
                                      ColorLegend, DownloadFile, ExperimentResult,
                                      FeatureStatisticsRow, JobStatus, StageStatus,
                                      TextureResult, TextureStatistics)
from backend.services import images
from backend.services.rendering import render_maps
from pipeline import run_experiment
from visualize import FEATURE_TITLES

_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="glcm")
_jobs = {}
_lock = threading.Lock()

FEATURE_DISPLAY = {"ASM": "ASM", "CON": "Contrast", "MEAN": "Mean"}


class AnalysisError(ValueError):
    pass


class AnalysisNotReady(Exception):
    pass


def _case_key_label(size):
    return (f"smooth_{size}", f"{size}x{size} smoothed") if size else ("original", "Original")


def _build_stages(smoothing_sizes):
    stages = [("load", "Loading image"),
              ("smoothing", "Applying " + " and ".join(f"{s}x{s}" for s in smoothing_sizes)
               + " averaging filters")]
    for size in [None, *smoothing_sizes]:
        key, label = _case_key_label(size)
        stages.append((f"{key}:glcm_features",
                       f"{label}: quantization, moving-window GLCM, ASM / Contrast / Mean"))
        stages.append((f"{key}:kmeans", f"{label}: K-Means clustering"))
    stages += [("statistics", "Computing statistics and comparison metrics"),
               ("figures", "Generating figures and comparison grid"),
               ("render", "Rendering texture maps for the viewer")]
    return [{"id": i, "label": label, "state": "pending"} for i, label in stages]


class Job:
    def __init__(self, analysis_id, params):
        self.id = analysis_id
        self.params = params
        self.state = "queued"
        self.stages = _build_stages(config.SMOOTHING_SIZES)
        self.error = None
        self.started = None
        self.finished = None

    def advance(self, stage_id):
        with _lock:
            for st in self.stages:
                if st["state"] == "active":
                    st["state"] = "done"
            for st in self.stages:
                if st["id"] == stage_id:
                    st["state"] = "active"

    def fail(self, message):
        with _lock:
            for st in self.stages:
                if st["state"] == "active":
                    st["state"] = "failed"
            self.state = "failed"
            self.error = message
            self.finished = time.time()

    def status(self):
        with _lock:
            elapsed = None
            if self.started:
                elapsed = (self.finished or time.time()) - self.started
            return JobStatus(analysis_id=self.id, state=self.state,
                             stages=[StageStatus(**s) for s in self.stages],
                             error=self.error, elapsed_seconds=elapsed)


def _valid(analysis_id):
    if not _ID_RE.match(analysis_id or ""):
        raise AnalysisError("Invalid analysis id")


def analysis_dir(analysis_id):
    _valid(analysis_id)
    return settings.ANALYSIS_DIR / analysis_id


# ---------------------------------------------------------------------------
# Job lifecycle
# ---------------------------------------------------------------------------

def start_analysis(params: AnalysisParameters):
    images.get_metadata(params.image_id)  # raises if the image does not exist
    analysis_id = uuid.uuid4().hex
    job = Job(analysis_id, params)
    with _lock:
        _jobs[analysis_id] = job
    _executor.submit(_run, job)
    return analysis_id


def _run(job: Job):
    p = job.params
    out = analysis_dir(job.id)
    try:
        job.started = time.time()
        job.state = "running"
        job.advance("load")
        image = images.load_source(p.image_id)

        def progress(stage, case):
            if stage == "done":
                return
            job.advance(f"{case}:{stage}" if case else stage)

        results, feature_stats, cluster_stats, metrics, interpretation = run_experiment(
            image, smoothing_sizes=config.SMOOTHING_SIZES, window_size=p.glcm_window_size,
            num_levels=p.gray_levels, distance=p.distance, angle=p.angle, k=p.clusters,
            random_state=p.random_state, output_dir=out, save=True, verbose=False,
            progress=progress)

        job.advance("render")
        legends = render_maps(results, out / "maps")
        job.finished = time.time()
        result = _build_result(job, results, feature_stats, cluster_stats, metrics,
                               interpretation, legends)
        (out / "result.json").write_text(result.model_dump_json(by_alias=True))
        with _lock:
            for st in job.stages:
                st["state"] = "done"
            job.state = "completed"
    except Exception as exc:  # report any pipeline failure to the client
        traceback.print_exc()
        job.fail(f"{type(exc).__name__}: {exc}")


def get_status(analysis_id):
    _valid(analysis_id)
    with _lock:
        job = _jobs.get(analysis_id)
    if job:
        return job.status()
    if (analysis_dir(analysis_id) / "result.json").exists():
        result = get_result(analysis_id)
        stages = [StageStatus(**{**s, "state": "done"})
                  for s in _build_stages(result.smoothing_sizes)]
        return JobStatus(analysis_id=analysis_id, state="completed", stages=stages,
                         elapsed_seconds=result.elapsed_seconds)
    raise AnalysisError("Analysis not found")


def get_result(analysis_id):
    path = analysis_dir(analysis_id) / "result.json"
    if not path.exists():
        with _lock:
            job = _jobs.get(analysis_id)
        if job is None:
            raise AnalysisError("Analysis not found")
        raise AnalysisNotReady(job.state)
    return AnalysisResult.model_validate(json.loads(path.read_text()))


# ---------------------------------------------------------------------------
# Result assembly
# ---------------------------------------------------------------------------

def _file_url(analysis_id, name):
    return f"/api/analysis/{analysis_id}/files/{name}"


def _build_result(job, results, feature_stats, cluster_stats, metrics, interpretation, legends):
    aid = job.id
    out = analysis_dir(aid)
    experiments = []
    for key, case in results.items():
        prefix = case["prefix"]
        textures = []
        for name in ("ASM", "CON", "MEAN"):
            v = case["features"][name]
            figure = out / f"{prefix}_{name}.png"
            textures.append(TextureResult(
                feature=name, title=FEATURE_DISPLAY[name],
                image_url=_file_url(aid, f"maps/{prefix}_{name}.png"),
                figure_url=_file_url(aid, figure.name) if figure.exists() else None,
                statistics=TextureStatistics(min=float(v.min()), max=float(v.max()),
                                             mean=float(v.mean()), std=float(v.std())),
                legend=ColorLegend(**legends[prefix][name]),
            ))
        cl = case["clusters"]
        total = int(cl["sizes"].sum())
        clusters = [ClusterStatistics(cluster=i, pixels=int(n), percent=100.0 * int(n) / total,
                                      center_asm=float(cl["centers"][i][0]),
                                      center_con=float(cl["centers"][i][1]),
                                      center_mean=float(cl["centers"][i][2]))
                    for i, n in enumerate(cl["sizes"])]
        experiments.append(ExperimentResult(
            key=key, label=case["label"], prefix=prefix, smoothing_size=case["smoothing_size"],
            input_image_url=_file_url(aid, f"{prefix}.png"),
            kmeans_image_url=_file_url(aid, f"maps/{prefix}_KMEANS.png"),
            kmeans_legend=ColorLegend(**legends[prefix]["KMEANS"]),
            textures=textures, clusters=clusters, inertia=float(cl["inertia"]),
        ))

    fstats = [FeatureStatisticsRow(case=r.Case, feature=r.Feature, min=r.Min, max=r.Max,
                                   mean=r.Mean, std=r.Std)
              for r in feature_stats.itertuples(index=False)]
    metric_rows = [{k: (v if isinstance(v, str) else float(v)) for k, v in row.items()}
                   for row in metrics.to_dict(orient="records")]
    grid = out / "comparison_grid.png"
    smooth = out / "smoothing_comparison.png"
    return AnalysisResult(
        analysis_id=aid, image=images.get_metadata(job.params.image_id), parameters=job.params,
        smoothing_sizes=list(config.SMOOTHING_SIZES), experiments=experiments,
        feature_statistics=fstats, metrics=metric_rows, interpretation=interpretation,
        comparison_grid_url=_file_url(aid, grid.name) if grid.exists() else None,
        smoothing_comparison_url=_file_url(aid, smooth.name) if smooth.exists() else None,
        downloads=list_downloads(aid, results),
        zip_url=f"/api/analysis/{aid}/download.zip",
        elapsed_seconds=(job.finished or time.time()) - (job.started or time.time()),
    )


def _describe(name, case_labels):
    """Human-readable label and category for a generated file name."""
    stem, suffix = Path(name).stem, Path(name).suffix.lower()
    if suffix == ".csv":
        return stem.replace("_", " ").capitalize() + " (CSV)", "table"
    if suffix == ".md":
        return "Interpretation (Markdown)", "text"
    for prefix, label in case_labels.items():
        if stem == prefix:
            return f"{label}: input image", "image"
        if stem.startswith(prefix + "_"):
            part = stem[len(prefix) + 1:]
            if part in FEATURE_TITLES:
                return f"{label}: {FEATURE_DISPLAY[part]} texture map", "texture"
            if part == "KMEANS":
                return f"{label}: K-Means cluster map", "cluster"
            if part == "textures":
                return f"{label}: texture panel (input + ASM / Contrast / Mean)", "figure"
            if part == "clusters":
                return f"{label}: cluster summary figure", "figure"
            if part == "summary":
                return f"{label}: image summary and histogram", "figure"
    figures = {"comparison_grid": "Final comparison grid (5 x 3)",
               "smoothing_comparison": "Smoothing comparison with histograms",
               "histograms": "Histogram overlay"}
    return figures.get(stem, stem.replace("_", " ")), "figure"


def list_downloads(analysis_id, results=None):
    """Files actually present in the analysis directory (top level only)."""
    out = analysis_dir(analysis_id)
    if results is not None:
        case_labels = {c["prefix"]: c["label"] for c in results.values()}
    else:
        case_labels = {"original": "Original",
                       **{f"smoothed_{s}x{s}": f"{s}x{s} smoothed" for s in config.SMOOTHING_SIZES}}
    order = {"image": 0, "texture": 1, "cluster": 2, "figure": 3, "table": 4, "text": 5}
    files = []
    for path in sorted(out.iterdir()):
        if not path.is_file() or path.name == "result.json":
            continue
        label, category = _describe(path.name, case_labels)
        files.append(DownloadFile(name=path.name, label=label, category=category,
                                  size_bytes=path.stat().st_size,
                                  url=_file_url(analysis_id, path.name)))
    files.sort(key=lambda f: (order[f.category], f.name))
    return files


def resolve_file(analysis_id, name):
    """Path of a generated file, refusing anything outside the analysis directory."""
    base = analysis_dir(analysis_id).resolve()
    target = (base / name).resolve()
    if base not in target.parents or not target.is_file() or target.name == "result.json":
        raise AnalysisError("File not found")
    return target


def build_zip(analysis_id):
    base = analysis_dir(analysis_id)
    if not (base / "result.json").exists():
        raise AnalysisError("Analysis not found or not finished")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(base.iterdir()):
            if path.is_file() and path.name != "result.json":
                zf.write(path, arcname=path.name)
    buf.seek(0)
    return buf
