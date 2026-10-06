"""End-to-end pipeline: quantise -> moving-window GLCM -> features -> K-Means,
applied to the original image and to its 7x7 / 9x9 box-smoothed versions."""

from pathlib import Path

import config
from analysis import (calculate_statistics, cluster_statistics, comparison_metrics,
                      interpret_results)
from clustering import cluster_features
from glcm import extract_texture_features
from preprocess import smooth_image
from visualize import visualize_results


def _notify(progress, stage, case=None):
    if progress is not None:
        progress(stage, case)


def process_image(image, window_size=config.GLCM_WINDOW_SIZE, num_levels=config.GRAY_LEVELS,
                  distance=config.DISTANCE, angle=config.ANGLE, k=config.NUM_CLUSTERS,
                  lo=None, hi=None, symmetric=config.SYMMETRIC, method="vectorized",
                  random_state=config.RANDOM_STATE, progress=None, case=None):
    """Run GLCM texture extraction and K-Means on one image.

    ``lo`` / ``hi`` fix the quantisation range (shared across experiments).
    ``progress(stage, case)`` is called, if given, before each stage
    ('glcm_features', 'kmeans').
    Returns a dict with 'quantized', 'features' (ASM / CON / MEAN images) and
    'clusters' (see ``cluster_features``).
    """
    _notify(progress, "glcm_features", case)
    feats = extract_texture_features(image, window_size, num_levels, distance, angle,
                                     lo=lo, hi=hi, symmetric=symmetric, method=method)
    q = feats.pop("quantized")
    _notify(progress, "kmeans", case)
    clusters = cluster_features(feats, k, random_state=random_state)
    return {"quantized": q, "features": feats, "clusters": clusters}


def run_experiment(image, smoothing_sizes=config.SMOOTHING_SIZES,
                   window_size=config.GLCM_WINDOW_SIZE, num_levels=config.GRAY_LEVELS,
                   distance=config.DISTANCE, angle=config.ANGLE, k=config.NUM_CLUSTERS,
                   symmetric=config.SYMMETRIC, output_dir=config.OUTPUT_DIR, save=True,
                   verbose=True, random_state=config.RANDOM_STATE, progress=None):
    """Process the original and every smoothed version with identical parameters.

    ``progress(stage, case_key)``, if given, receives stage events:
    'smoothing', then per case 'glcm_features' and 'kmeans', then
    'statistics', 'figures' and 'done' (case_key is None for global stages).

    Returns (results, feature_stats, cluster_stats, metrics, interpretation).
    ``results`` maps a case key to a dict with 'label', 'prefix',
    'smoothing_size', 'image', 'quantized', 'features', 'clusters'.
    """
    _notify(progress, "smoothing")
    # The original image's range defines the gray-level bins for every case.
    lo, hi = float(image.min()), float(image.max())
    cases = [("original", "Original", "original", None, image)]
    for s in smoothing_sizes:
        cases.append((f"smooth_{s}", f"{s}x{s} smoothed", f"smoothed_{s}x{s}", s,
                      smooth_image(image, s)))

    results = {}
    for key, label, prefix, size, img in cases:
        if verbose:
            print(f"[{label}] GLCM window {window_size}x{window_size}, L={num_levels}, "
                  f"d={distance}, angle={angle}, K={k}")
        res = process_image(img, window_size, num_levels, distance, angle, k,
                            lo=lo, hi=hi, symmetric=symmetric, random_state=random_state,
                            progress=progress, case=key)
        res.update(label=label, prefix=prefix, smoothing_size=size, image=img)
        results[key] = res

    _notify(progress, "statistics")
    feature_stats = calculate_statistics(results)
    cluster_stats = cluster_statistics(results)
    metrics = comparison_metrics(results)
    interpretation = (interpret_results(results, feature_stats, cluster_stats, metrics)
                      if len(results) >= 3 else "")

    if save:
        _notify(progress, "figures")
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        visualize_results(results, out)
        feature_stats.to_csv(out / "feature_statistics.csv", index=False, float_format="%.6f")
        cluster_stats.to_csv(out / "cluster_statistics.csv", index=False, float_format="%.6f")
        metrics.to_csv(out / "comparison_metrics.csv", index=False, float_format="%.6f")
        (out / "interpretation.md").write_text(interpretation + "\n")
        if verbose:
            print(f"Outputs written to {out}")
    _notify(progress, "done")
    return results, feature_stats, cluster_stats, metrics, interpretation
