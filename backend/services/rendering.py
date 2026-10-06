"""Viewer images: texture and cluster maps without axes, plus legend data.

Uses the colour maps, shared limits and cluster colours from the existing
``visualize`` module so the web viewer matches the report figures.
"""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_hex

from config import FEATURE_NAMES
from visualize import CLUSTER_COLORS, FEATURE_CMAPS, feature_limits

LEGEND_STOPS = 16


def _colormap_stops(name, n=LEGEND_STOPS):
    cmap = matplotlib.colormaps[name]
    return [to_hex(cmap(x)) for x in np.linspace(0, 1, n)]


def render_maps(results, maps_dir):
    """Write ``maps/{prefix}_{ASM|CON|MEAN|KMEANS}.png`` and return legend info.

    Returns ``{prefix: {"ASM": legend, "CON": legend, "MEAN": legend, "KMEANS": legend}}``
    where each legend is a dict compatible with ``ColorLegend``.
    """
    maps_dir = Path(maps_dir)
    maps_dir.mkdir(parents=True, exist_ok=True)
    limits = feature_limits(results)
    out = {}
    for case in results.values():
        prefix = case["prefix"]
        legends = {}
        for name in FEATURE_NAMES:
            data = case["features"][name]
            vmin, vmax = limits[name]
            cmap = FEATURE_CMAPS[name]
            plt.imsave(maps_dir / f"{prefix}_{name}.png", data, cmap=cmap, vmin=vmin, vmax=vmax)
            legends[name] = {
                "kind": "continuous", "colormap": cmap, "vmin": vmin, "vmax": vmax,
                "clipped_max": bool(np.max(data) > vmax + 1e-12),
                "colors": _colormap_stops(cmap),
            }

        labels = case["clusters"]["labels"]
        k = len(case["clusters"]["sizes"])
        palette = np.array([matplotlib.colors.to_rgb(c) for c in CLUSTER_COLORS[:k]])
        plt.imsave(maps_dir / f"{prefix}_KMEANS.png", palette[labels])
        legends["KMEANS"] = {
            "kind": "categorical", "colors": list(CLUSTER_COLORS[:k]),
            "labels": [f"Cluster {i}" for i in range(k)],
        }
        out[prefix] = legends
    return out
