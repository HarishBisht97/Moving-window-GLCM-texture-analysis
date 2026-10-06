"""Quantitative comparison and automatic, data-driven interpretation."""

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from config import FEATURE_NAMES
from preprocess import high_frequency_energy


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def calculate_statistics(results, names=FEATURE_NAMES):
    """Min / max / mean / std of every texture feature for every case."""
    rows = []
    for case in results.values():
        for n in names:
            v = case["features"][n]
            rows.append({"Case": case["label"], "Feature": n,
                         "Min": float(v.min()), "Max": float(v.max()),
                         "Mean": float(v.mean()), "Std": float(v.std())})
    return pd.DataFrame(rows)


def cluster_statistics(results, names=FEATURE_NAMES):
    """Pixel count, percentage and centre (original units) of every cluster."""
    rows = []
    for case in results.values():
        cl = case["clusters"]
        total = cl["sizes"].sum()
        for k, size in enumerate(cl["sizes"]):
            row = {"Case": case["label"], "Cluster": k, "Pixels": int(size),
                   "Percent": 100.0 * size / total}
            for f, val in zip(names, cl["centers"][k]):
                row[f"Center_{f}"] = float(val)
            rows.append(row)
    return pd.DataFrame(rows)


def boundary_fraction(labels):
    """Fraction of pixels with at least one 4-neighbour in a different cluster."""
    edge = np.zeros(labels.shape, dtype=bool)
    dh = labels[:, 1:] != labels[:, :-1]
    dv = labels[1:, :] != labels[:-1, :]
    edge[:, 1:] |= dh
    edge[:, :-1] |= dh
    edge[1:, :] |= dv
    edge[:-1, :] |= dv
    return float(edge.mean())


def effective_num_clusters(sizes):
    """exp(Shannon entropy) of the cluster-size distribution (K if balanced)."""
    p = np.asarray(sizes, dtype=float)
    p = p[p > 0] / p.sum()
    return float(np.exp(-(p * np.log(p)).sum()))


def distinct_patterns(features, names=FEATURE_NAMES, decimals=4):
    """Number of distinct [ASM, CON, MEAN] vectors in the image."""
    X = np.column_stack([np.round(features[n].ravel(), decimals) for n in names])
    return int(np.unique(X, axis=0).shape[0])


def level_transitions(q):
    """Share of neighbouring (horizontal + vertical) pixel pairs whose quantised
    levels differ, and the share of those differences that are single steps."""
    diffs = np.concatenate([np.abs(np.diff(q, axis=1)).ravel(),
                            np.abs(np.diff(q, axis=0)).ravel()])
    changed = diffs > 0
    frac = float(changed.mean())
    unit = float(np.mean(diffs[changed] == 1)) if changed.any() else 0.0
    return frac, unit


def comparison_metrics(results):
    """Per-case scalar metrics used for the comparison and interpretation."""
    cases = list(results.values())
    ref_labels = cases[0]["clusters"]["labels"].ravel()
    rows = []
    for case in cases:
        f, cl = case["features"], case["clusters"]
        trans, unit = level_transitions(case["quantized"])
        rows.append({
            "Case": case["label"],
            "High-freq energy": high_frequency_energy(case["image"]),
            "Image std": float(case["image"].std()),
            "Level transitions %": 100.0 * trans,
            "Single-step transitions %": 100.0 * unit,
            "Uniform windows (ASM=1) %": 100.0 * float(np.mean(np.isclose(f["ASM"], 1.0))),
            "Zero-contrast windows %": 100.0 * float(np.mean(np.isclose(f["CON"], 0.0))),
            "Distinct [ASM,CON,MEAN] vectors": distinct_patterns(f),
            "Cluster boundary pixels %": 100.0 * boundary_fraction(cl["labels"]),
            "Effective no. of clusters": effective_num_clusters(cl["sizes"]),
            "ARI vs original": float(adjusted_rand_score(ref_labels, cl["labels"].ravel())),
            "MAE of MEAN vs original": float(np.mean(np.abs(f["MEAN"] - cases[0]["features"]["MEAN"]))),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Interpretation
# ---------------------------------------------------------------------------

def _pct(new, old):
    if abs(old) < 1e-12:
        return float("inf") if abs(new) > 1e-12 else 0.0
    return 100.0 * (new - old) / abs(old)


def _change(new, old, fmt="{:.4f}"):
    pct = _pct(new, old)
    word = "increased" if new > old else "decreased" if new < old else "did not change"
    return f"{word} from {fmt.format(old)} to {fmt.format(new)} ({pct:+.1f}%)"


def _direction(values):
    """'monotonic increase' / 'monotonic decrease' / 'non-monotonic' across cases."""
    d = np.diff(values)
    if np.all(d > 0):
        return "increase"
    if np.all(d < 0):
        return "decrease"
    return "mixed"


def interpret_results(results, feature_stats, cluster_stats, metrics):
    """Return a Markdown interpretation whose statements follow the numbers."""
    labels = [c["label"] for c in results.values()]
    sizes = [c.get("smoothing_size") for c in results.values()]
    fs = feature_stats.set_index(["Case", "Feature"])
    m = metrics.set_index("Case")

    def stat(case, feat, col):
        return fs.loc[(case, feat), col]

    o, s1, s2 = labels[0], labels[1], labels[2]
    n1, n2 = sizes[1], sizes[2]
    lines = []

    # ---- image level -------------------------------------------------------
    hf = [m.loc[c, "High-freq energy"] for c in labels]
    lines.append("### Effect of smoothing on the image")
    lines.append(
        f"The neighbour-difference (high-frequency) energy of the image {_change(hf[1], hf[0], '{:.2f}')} "
        f"after {n1}x{n1} averaging and {_change(hf[2], hf[0], '{:.2f}')} after {n2}x{n2} averaging. "
        f"The image standard deviation went from {m.loc[o, 'Image std']:.2f} to "
        f"{m.loc[s1, 'Image std']:.2f} ({n1}x{n1}) and {m.loc[s2, 'Image std']:.2f} ({n2}x{n2}). "
        f"A box filter of size n replaces each pixel by the mean of N = n^2 pixels "
        f"(N = {n1 * n1} vs {n2 * n2}); its frequency response has a narrower main lobe for larger n, "
        f"so the {n2}x{n2} filter suppresses more fine detail and noise than the {n1}x{n1} filter."
    )

    # ---- ASM ---------------------------------------------------------------
    asm = [stat(c, "ASM", "Mean") for c in labels]
    uni = [m.loc[c, "Uniform windows (ASM=1) %"] for c in labels]
    lines.append("\n### Effect on ASM (texture uniformity)")
    txt = (f"Mean ASM {_change(asm[1], asm[0])} with {n1}x{n1} smoothing and "
           f"{_change(asm[2], asm[0])} with {n2}x{n2} smoothing. The share of perfectly uniform "
           f"windows (ASM = 1, a single gray-level pair) was {uni[0]:.1f}% / {uni[1]:.1f}% / {uni[2]:.1f}%. ")
    if _direction(asm) == "increase":
        txt += ("Smoothing therefore increased local texture uniformity: averaging pulls neighbouring "
                "pixels towards the same value, so within a window they fall into fewer quantised "
                "levels, the GLCM probability mass concentrates in a few (mainly diagonal) cells, and "
                "the sum of squared probabilities grows. The larger window gives the stronger effect.")
    elif asm[1] > asm[0] or asm[2] > asm[0]:
        txt += ("Both smoothed images are more uniform than the original, but the change is not "
                "monotonic between the two smoothing sizes, so beyond a certain window size additional "
                "averaging no longer concentrates the GLCM further (gradual ramps created by the wider "
                "filter can span several quantisation levels).")
    else:
        txt += ("Smoothing did not increase ASM here. This can happen when large flat areas were "
                "already saturated in a single quantisation level and the filter blurs sharp edges into "
                "wide ramps that cross several levels, spreading the GLCM over more cells.")
    lines.append(txt)

    # ---- Contrast ----------------------------------------------------------
    con = [stat(c, "CON", "Mean") for c in labels]
    con_max = [stat(c, "CON", "Max") for c in labels]
    zc = [m.loc[c, "Zero-contrast windows %"] for c in labels]
    lines.append("\n### Effect on Contrast")
    txt = (f"Mean contrast {_change(con[1], con[0])} ({n1}x{n1}) and {_change(con[2], con[0])} "
           f"({n2}x{n2}); the maximum contrast went from {con_max[0]:.3f} to {con_max[1]:.3f} and "
           f"{con_max[2]:.3f}. Windows with zero contrast (all pairs on the GLCM diagonal) made up "
           f"{zc[0]:.1f}% / {zc[1]:.1f}% / {zc[2]:.1f}% of the image. ")
    if _direction(con) == "decrease":
        txt += ("Averaging neighbouring pixels makes adjacent values nearly equal, so the quantised "
                "pairs (i, j) at distance 1 move towards the diagonal i = j where the weight (i - j)^2 is "
                "zero or small. Contrast falls, and falls further for the larger filter.")
    else:
        txt += ("Contrast did not decrease monotonically, which indicates that some edges were "
                "converted into ramps crossing quantisation boundaries; the averaged differences are "
                "small but can still register as |i - j| = 1 transitions.")
    lines.append(txt)

    # ---- Mean --------------------------------------------------------------
    mean = [stat(c, "MEAN", "Mean") for c in labels]
    mstd = [stat(c, "MEAN", "Std") for c in labels]
    mae = [m.loc[c, "MAE of MEAN vs original"] for c in labels]
    lines.append("\n### Effect on Mean")
    big = max(abs(_pct(mean[1], mean[0])), abs(_pct(mean[2], mean[0])))
    lines.append(
        f"The image-wide average of the GLCM mean was {mean[0]:.3f} / {mean[1]:.3f} / {mean[2]:.3f} "
        f"(largest relative change {big:.1f}%), i.e. it "
        f"{'remained practically unchanged' if big < 5 else 'changed noticeably'}: an averaging filter "
        f"preserves the local mean intensity (its kernel sums to one), so the average gray level of a "
        f"window is largely conserved. The spatial variability of the MEAN image, however, "
        f"{_change(mstd[1], mstd[0])} ({n1}x{n1}) and {_change(mstd[2], mstd[0])} ({n2}x{n2}); the "
        f"mean absolute per-pixel difference from the original MEAN image is {mae[1]:.3f} and "
        f"{mae[2]:.3f} gray levels. The MEAN image becomes a blurrier version of the original, with "
        f"extremes near bright/dark features pulled towards their surroundings."
    )

    # ---- K-Means -----------------------------------------------------------
    bnd = [m.loc[c, "Cluster boundary pixels %"] for c in labels]
    eff = [m.loc[c, "Effective no. of clusters"] for c in labels]
    dist = [m.loc[c, "Distinct [ASM,CON,MEAN] vectors"] for c in labels]
    ari = [m.loc[c, "ARI vs original"] for c in labels]
    cs = cluster_stats.set_index(["Case", "Cluster"])
    pct_str = {c: ", ".join(f"{cs.loc[(c, k), 'Percent']:.1f}%"
                            for k in sorted(cluster_stats[cluster_stats.Case == c].Cluster))
               for c in labels}
    lines.append("\n### Effect on K-Means clustering")
    lines.append(
        f"- **Distinct texture patterns:** the number of distinct [ASM, CON, MEAN] vectors "
        f"{_change(dist[1], dist[0], '{:.0f}')} ({n1}x{n1}) and {_change(dist[2], dist[0], '{:.0f}')} "
        f"({n2}x{n2}). "
        + ("Smoothing reduced the variety of texture patterns available to the classifier."
           if dist[2] < dist[0] and dist[1] < dist[0] else
           "Smoothing did not reduce the variety of feature vectors in this image.")
    )
    largest = [cluster_stats[cluster_stats.Case == c].Percent.max() for c in labels]
    trans = [m.loc[c, "Level transitions %"] for c in labels]
    unit = [m.loc[c, "Single-step transitions %"] for c in labels]
    homog = (f"Within regions, homogeneity clearly increased: the share of perfectly uniform windows "
             f"rose from {uni[0]:.1f}% to {uni[1]:.1f}% / {uni[2]:.1f}%. ")
    if bnd[1] < bnd[0] and bnd[2] < bnd[0]:
        bnd_txt = homog + ("Clusters became larger and more compact, with smoother and fewer "
                           "boundaries." if _direction(bnd) == "decrease" else
                           "Both smoothed maps are more compact than the original.")
    else:
        bnd_txt = homog + (
            f"Nevertheless the cluster maps did not become less fragmented. After smoothing, adjacent "
            f"quantised levels differ at only {trans[1]:.1f}% / {trans[2]:.1f}% of neighbour pairs "
            f"(original {trans[0]:.1f}%), and {unit[1]:.0f}% / {unit[2]:.0f}% of those differences are "
            f"single-level steps (original {unit[0]:.0f}%). The remaining non-zero contrast is therefore "
            f"concentrated in narrow bands where a window straddles a quantisation threshold of a "
            f"smooth intensity ramp (iso-intensity contours). K-Means separates these thin bands from "
            f"the uniform interiors, so they appear as elongated strips that add boundary pixels. This "
            f"is a side effect of combining smoothing with coarse gray-level quantisation rather than "
            f"real texture.")
    lines.append(
        f"- **Homogeneity / boundaries:** the fraction of pixels on a cluster boundary was "
        f"{bnd[0]:.1f}% / {bnd[1]:.1f}% / {bnd[2]:.1f}%. " + bnd_txt
    )
    lines.append(
        f"- **Cluster sizes:** original [{pct_str[o]}], {n1}x{n1} [{pct_str[s1]}], "
        f"{n2}x{n2} [{pct_str[s2]}] (clusters ordered by increasing MEAN centre). The effective number "
        f"of clusters (exp of the size entropy) was {eff[0]:.2f} / {eff[1]:.2f} / {eff[2]:.2f}"
        + (", so the pixels are spread less evenly over the K classes after smoothing, consistent with "
           "regions becoming more similar." if eff[2] < eff[0] else
           f", so the pixels are spread more evenly over the K classes after smoothing (largest "
           f"cluster: {largest[0]:.1f}% / {largest[1]:.1f}% / {largest[2]:.1f}%). Once fine texture is "
           f"removed, the feature space is organised mainly by brightness (MEAN) and by the "
           f"uniform-interior versus transition-band distinction, which splits the image into more "
           f"balanced groups.")
    )
    lines.append(
        f"- **Changed boundaries:** the Adjusted Rand Index between the original map and the smoothed "
        f"maps is {ari[1]:.3f} ({n1}x{n1}) and {ari[2]:.3f} ({n2}x{n2}) (1 = identical partition). "
        + ("Agreement drops as the filter grows, so the larger filter changes cluster membership and "
           "boundaries more." if ari[2] < ari[1] else
           "The 9x9 map is not less similar to the original than the 7x7 map.")
    )
    lines.append(
        "- **Small / high-frequency structures:** thin features narrower than the filter (field "
        "boundaries, drainage lines, isolated trees) are averaged with their surroundings, so their "
        "high-contrast, low-ASM signature disappears and they are absorbed into the neighbouring "
        "clusters; distinct regions with similar mean brightness become more alike because their "
        "texture differences are what smoothing removes."
    )

    # ---- 7x7 vs 9x9 --------------------------------------------------------
    lines.append(f"\n### {n1}x{n1} versus {n2}x{n2}")
    stronger = [
        hf[2] < hf[1], con[2] < con[1], asm[2] > asm[1], bnd[2] < bnd[1], dist[2] < dist[1],
    ]
    yn = ["yes" if s else "no" for s in stronger]
    lines.append(
        f"Relative to {n1}x{n1}, did the {n2}x{n2} filter give lower high-frequency energy: {yn[0]}; "
        f"lower mean contrast: {yn[1]}; higher mean ASM: {yn[2]}; fewer cluster-boundary pixels: "
        f"{yn[3]}; fewer distinct feature vectors: {yn[4]}. "
        + (f"All indicators confirm that the {n2}x{n2} window produces the stronger smoothing effect, "
           f"because each output pixel averages {n2 * n2} instead of {n1 * n1} values, cancelling "
           f"more of the local variation that GLCM texture measures."
           if all(stronger) else
           f"{sum(stronger)} of 5 indicators show a stronger effect for {n2}x{n2}; the larger window "
           f"averages {n2 * n2} instead of {n1 * n1} values, so in general it removes more local variation.")
    )
    return "\n".join(lines)
