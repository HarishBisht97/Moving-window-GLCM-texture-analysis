"""Figures: input summary, texture images, cluster maps, smoothing, comparison grid."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
from PIL import Image

from config import FEATURE_NAMES
from preprocess import to_uint8

FEATURE_CMAPS = {"ASM": "viridis", "CON": "inferno", "MEAN": "gray"}
FEATURE_TITLES = {"ASM": "ASM (Angular Second Moment)", "CON": "Contrast", "MEAN": "GLCM Mean"}
CLUSTER_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                  "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]


def cluster_cmap(k):
    cmap = ListedColormap(CLUSTER_COLORS[:k])
    norm = BoundaryNorm(np.arange(-0.5, k + 0.5, 1), k)
    return cmap, norm


def _finish(fig, path, show):
    if path is not None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=130, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)


def gray_range(image):
    """Display range for a grayscale image: 0..255 for 8-bit data, else its own min..max."""
    lo, hi = float(np.min(image)), float(np.max(image))
    if lo >= 0 and hi <= 255:
        return 0.0, 255.0
    return lo, hi


def save_gray_png(image, path, lo=0, hi=255):
    """Save a grayscale array as an 8-bit PNG (fixed range keeps cases comparable)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(to_uint8(image, lo, hi)).save(path)


def feature_limits(results, names=FEATURE_NAMES, upper_percentile=99.5):
    """Shared (vmin, vmax) per feature across all cases for fair visual comparison.

    The upper limit is a high percentile of the pooled values so that a few
    extreme windows do not compress the colour scale of every other pixel.
    """
    lim = {}
    for n in names:
        vals = [c["features"][n] for c in results.values()]
        hi = max(float(np.percentile(v, upper_percentile)) for v in vals)
        lo = min(float(v.min()) for v in vals)
        lim[n] = (lo, hi if hi > lo else lo + 1e-9)
    return lim


def plot_input_summary(image, title="Input image", path=None, show=False, vrange=None):
    """Image with dimensions / min / max and its histogram."""
    vr = vrange or gray_range(image)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
    ax[0].imshow(image, cmap="gray", vmin=vr[0], vmax=vr[1])
    ax[0].set_title(f"{title}\n{image.shape[1]} x {image.shape[0]} px, "
                    f"min {image.min():.1f}, max {image.max():.1f}")
    ax[0].axis("off")
    ax[1].hist(image.ravel(), bins=256, range=vr, color="0.3")
    ax[1].set_title("Histogram")
    ax[1].set_xlabel("Gray value")
    ax[1].set_ylabel("Pixel count")
    fig.tight_layout()
    _finish(fig, path, show)


def plot_quantized(image, q, num_levels, path=None, show=False, vrange=None):
    vr = vrange or gray_range(image)
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.5))
    ax[0].imshow(image, cmap="gray", vmin=vr[0], vmax=vr[1])
    ax[0].set_title("Original (full gray range)")
    im = ax[1].imshow(q, cmap="gray", vmin=0, vmax=num_levels - 1)
    ax[1].set_title(f"Quantised ({num_levels} levels)")
    fig.colorbar(im, ax=ax[1], fraction=0.046, pad=0.04)
    for a in ax[:2]:
        a.axis("off")
    ax[2].bar(np.arange(num_levels), np.bincount(q.ravel(), minlength=num_levels), color="0.3")
    ax[2].set_title("Quantised histogram")
    ax[2].set_xlabel("Gray level")
    fig.tight_layout()
    _finish(fig, path, show)


def save_feature_image(feature, name, path, vmin=None, vmax=None):
    """Save one texture image with a colorbar."""
    fig, ax = plt.subplots(figsize=(6, 5.2))
    im = ax.imshow(feature, cmap=FEATURE_CMAPS.get(name, "viridis"), vmin=vmin, vmax=vmax)
    ax.set_title(FEATURE_TITLES.get(name, name))
    ax.axis("off")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    _finish(fig, path, show=False)


def plot_texture_set(case, limits=None, path=None, show=False, vrange=None):
    """Input image + ASM, Contrast, Mean texture images with colorbars."""
    vr = vrange or gray_range(case["image"])
    fig, ax = plt.subplots(1, 4, figsize=(20, 4.8))
    ax[0].imshow(case["image"], cmap="gray", vmin=vr[0], vmax=vr[1])
    ax[0].set_title(f"{case['label']}: input")
    ax[0].axis("off")
    for a, n in zip(ax[1:], FEATURE_NAMES):
        vmin, vmax = limits[n] if limits else (None, None)
        im = a.imshow(case["features"][n], cmap=FEATURE_CMAPS[n], vmin=vmin, vmax=vmax)
        a.set_title(FEATURE_TITLES[n])
        a.axis("off")
        fig.colorbar(im, ax=a, fraction=0.046, pad=0.04)
    fig.tight_layout()
    _finish(fig, path, show)


def save_cluster_map(labels, k, path, title="K-Means texture clusters"):
    cmap, norm = cluster_cmap(k)
    fig, ax = plt.subplots(figsize=(6, 5.6))
    ax.imshow(labels, cmap=cmap, norm=norm, interpolation="nearest")
    ax.set_title(title)
    ax.axis("off")
    ax.legend(handles=[Patch(color=CLUSTER_COLORS[i], label=f"Cluster {i}") for i in range(k)],
              loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=min(k, 5), frameon=False)
    _finish(fig, path, show=False)


def plot_clusters(case, path=None, show=False, vrange=None):
    """Original beside cluster map, cluster sizes, and centres in feature space."""
    vr = vrange or gray_range(case["image"])
    cl = case["clusters"]
    k = len(cl["sizes"])
    cmap, norm = cluster_cmap(k)
    fig = plt.figure(figsize=(20, 5))
    gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 0.9, 1.1])

    a0 = fig.add_subplot(gs[0])
    a0.imshow(case["image"], cmap="gray", vmin=vr[0], vmax=vr[1])
    a0.set_title(f"{case['label']}: input")
    a0.axis("off")

    a1 = fig.add_subplot(gs[1])
    a1.imshow(cl["labels"], cmap=cmap, norm=norm, interpolation="nearest")
    a1.set_title(f"K-Means (K={k}) on [ASM, CON, MEAN]")
    a1.axis("off")

    a2 = fig.add_subplot(gs[2])
    pct = 100 * cl["sizes"] / cl["sizes"].sum()
    bars = a2.bar(np.arange(k), cl["sizes"], color=CLUSTER_COLORS[:k])
    for b, p in zip(bars, pct):
        a2.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{p:.1f}%",
                ha="center", va="bottom", fontsize=9)
    a2.set_xticks(np.arange(k))
    a2.set_xlabel("Cluster")
    a2.set_ylabel("Pixels")
    a2.set_title("Cluster sizes")

    a3 = fig.add_subplot(gs[3])
    a3.axis("off")
    cell = [[f"{i}"] + [f"{v:.3f}" for v in cl["centers"][i]] + [f"{cl['sizes'][i]}"]
            for i in range(k)]
    tbl = a3.table(cellText=cell, colLabels=["Cluster", *cl["feature_names"], "Pixels"],
                   loc="center", cellLoc="center")
    tbl.scale(1, 1.6)
    for i in range(k):
        tbl[(i + 1, 0)].set_facecolor(CLUSTER_COLORS[i])
    a3.set_title("Cluster centres (feature units)")
    fig.tight_layout()
    _finish(fig, path, show)


def plot_smoothing(images, path=None, show=False, vrange=None):
    """Images (top row) and histograms (bottom row) of original and smoothed cases."""
    n = len(images)
    vr = vrange or gray_range(next(iter(images.values())))
    fig, ax = plt.subplots(2, n, figsize=(5.5 * n, 9))
    for j, (label, img) in enumerate(images.items()):
        ax[0, j].imshow(img, cmap="gray", vmin=vr[0], vmax=vr[1])
        ax[0, j].set_title(f"{label}\nmin {img.min():.1f}, max {img.max():.1f}, std {img.std():.1f}")
        ax[0, j].axis("off")
        ax[1, j].hist(img.ravel(), bins=128, range=vr, color="0.3")
        ax[1, j].set_title(f"Histogram: {label}")
        ax[1, j].set_xlabel("Gray value")
    fig.tight_layout()
    _finish(fig, path, show)


def plot_histograms(images, path=None, show=False, vrange=None):
    """Overlayed histograms of all cases."""
    vr = vrange or gray_range(next(iter(images.values())))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for label, img in images.items():
        ax.hist(img.ravel(), bins=128, range=vr, histtype="step", lw=1.5, label=label)
    ax.set_xlabel("Gray value")
    ax.set_ylabel("Pixel count")
    ax.set_title("Histograms: original vs smoothed")
    ax.legend()
    fig.tight_layout()
    _finish(fig, path, show)


def plot_comparison_grid(results, path=None, show=False, vrange=None):
    """5 x N grid: rows Input / ASM / Contrast / Mean / K-Means, columns = cases.

    Each feature row shares a colour scale across cases so that brightness
    differences reflect real numerical differences.
    """
    cases = list(results.values())
    vr = vrange or gray_range(cases[0]["image"])
    lim = feature_limits(results)
    k = len(cases[0]["clusters"]["sizes"])
    cmap_k, norm_k = cluster_cmap(k)
    rows = ["Input", *FEATURE_NAMES, "K-Means"]
    fig, ax = plt.subplots(len(rows), len(cases), figsize=(4.4 * len(cases) + 1.5, 4.2 * len(rows)),
                           layout="constrained")
    for j, case in enumerate(cases):
        ax[0, j].set_title(case["label"], fontsize=15, fontweight="bold")
        ax[0, j].imshow(case["image"], cmap="gray", vmin=vr[0], vmax=vr[1])
        for i, n in enumerate(FEATURE_NAMES, start=1):
            im = ax[i, j].imshow(case["features"][n], cmap=FEATURE_CMAPS[n],
                                 vmin=lim[n][0], vmax=lim[n][1])
            if j == len(cases) - 1:
                fig.colorbar(im, ax=ax[i, :].tolist(), shrink=0.9, pad=0.01,
                             extend="max" if n == "CON" else "neither")
        ax[-1, j].imshow(case["clusters"]["labels"], cmap=cmap_k, norm=norm_k,
                         interpolation="nearest")
    for i, r in enumerate(rows):
        for j in range(len(cases)):
            ax[i, j].set_xticks([])
            ax[i, j].set_yticks([])
        ax[i, 0].set_ylabel(FEATURE_TITLES.get(r, r), fontsize=13)
    fig.legend(handles=[Patch(color=CLUSTER_COLORS[c], label=f"Cluster {c}") for c in range(k)],
               loc="outside lower center", ncol=k, frameon=False, fontsize=12)
    _finish(fig, path, show)


def visualize_results(results, output_dir, show=False):
    """Write every per-case and comparison figure to ``output_dir``."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    lim = feature_limits(results)
    first = next(iter(results.values()))
    vr = gray_range(first["image"])
    for case in results.values():
        prefix = case["prefix"]
        save_gray_png(case["image"], out / f"{prefix}.png", *vr)
        for n in FEATURE_NAMES:
            save_feature_image(case["features"][n], n, out / f"{prefix}_{n}.png", *lim[n])
        save_cluster_map(case["clusters"]["labels"], len(case["clusters"]["sizes"]),
                         out / f"{prefix}_KMEANS.png", title=f"{case['label']}: K-Means clusters")
        plot_texture_set(case, lim, out / f"{prefix}_textures.png", show, vrange=vr)
        plot_clusters(case, out / f"{prefix}_clusters.png", show, vrange=vr)

    images = {c["label"]: c["image"] for c in results.values()}
    plot_input_summary(first["image"], "Original image", out / "original_summary.png", show, vr)
    plot_smoothing(images, out / "smoothing_comparison.png", show, vr)
    plot_histograms(images, out / "histograms.png", show, vr)
    plot_comparison_grid(results, out / "comparison_grid.png", show, vr)
