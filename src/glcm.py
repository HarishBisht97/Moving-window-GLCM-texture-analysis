"""Manual moving-window Gray Level Co-occurrence Matrix (GLCM) texture analysis.

The GLCM is computed LOCALLY: for every pixel a window of size w x w centred on
that pixel is taken, its own GLCM is built and normalised, and the texture
features ASM, Contrast and Mean are derived from that local GLCM. The feature
value is written to the centre pixel of the window, producing one texture image
per feature.

Two implementations are provided:

* ``moving_window_glcm_naive`` -- the reference implementation. It literally
  slides the window pixel by pixel, calls ``compute_glcm`` on the patch,
  normalises it and evaluates the feature formulas.
* ``moving_window_glcm`` -- an optimised implementation that produces exactly
  the same local GLCMs. Each pixel pair (p, p + offset) is encoded as a single
  integer ``k = i * L + j``; for every code k an indicator image is box-summed
  over the window with an integral image. The box sum at (r, c) is the GLCM
  entry (i, j) of the window centred at (r, c).

Conventions
-----------
* Gray levels are integers 0 .. L-1 after quantisation.
* Offset (dr, dc) means the neighbour of pixel (r, c) is (r + dr, c + dc).
  Angle 0 deg with distance 1 gives offset (0, 1), i.e. the right neighbour.
* GLCM[i, j] counts pairs whose reference pixel has level i and whose
  neighbour has level j. Only pairs where BOTH pixels lie inside the window
  are counted.
* Boundaries: the quantised image is reflect-padded by w // 2 so every output
  pixel has a full window and the texture images have the input's size.
"""

import numpy as np


# ---------------------------------------------------------------------------
# Quantisation and spatial relationship
# ---------------------------------------------------------------------------

def quantize_image(image, num_levels, lo=None, hi=None):
    """Map intensities linearly to integer gray levels 0 .. num_levels-1.

    ``q = floor((I - lo) / (hi - lo) * L)``, clipped to [0, L-1].

    ``lo`` / ``hi`` default to the image's own min / max. Passing a fixed range
    (e.g. that of the original image) makes quantisation identical across
    experiments, so a level always denotes the same intensity band.
    """
    image = np.asarray(image, dtype=np.float64)
    lo = float(image.min()) if lo is None else float(lo)
    hi = float(image.max()) if hi is None else float(hi)
    if hi <= lo:
        return np.zeros(image.shape, dtype=np.int32)
    q = np.floor((image - lo) / (hi - lo) * num_levels)
    return np.clip(q, 0, num_levels - 1).astype(np.int32)


def angle_to_offset(distance, angle):
    """Return the (row, col) offset for a GLCM distance and angle in degrees."""
    offsets = {
        0: (0, distance),
        45: (-distance, distance),
        90: (-distance, 0),
        135: (-distance, -distance),
    }
    angle = int(angle) % 180
    if angle not in offsets:
        raise ValueError(f"Angle must be one of 0, 45, 90, 135 (got {angle}).")
    return offsets[angle]


# ---------------------------------------------------------------------------
# Single-window GLCM and features
# ---------------------------------------------------------------------------

def _pair_slices(shape, offset):
    """Slices selecting reference pixels and their neighbours inside ``shape``."""
    h, w = shape
    dr, dc = offset
    ref = (slice(max(0, -dr), h - max(0, dr)), slice(max(0, -dc), w - max(0, dc)))
    nbr = (slice(max(0, dr), h - max(0, -dr)), slice(max(0, dc), w - max(0, -dc)))
    return ref, nbr


def compute_glcm(patch, num_levels, offset=(0, 1), symmetric=False):
    """Count co-occurrences of gray-level pairs inside one quantised patch.

    Returns an integer (L, L) matrix where entry (i, j) is the number of
    pixel pairs (p, p + offset), both inside the patch, with levels (i, j).
    """
    patch = np.asarray(patch)
    glcm = np.zeros((num_levels, num_levels), dtype=np.int64)
    ref_sl, nbr_sl = _pair_slices(patch.shape, offset)
    ref = patch[ref_sl].ravel()
    nbr = patch[nbr_sl].ravel()
    np.add.at(glcm, (ref, nbr), 1)
    if symmetric:
        glcm = glcm + glcm.T
    return glcm


def normalize_glcm(glcm):
    """P(i, j) = GLCM(i, j) / sum(GLCM). All-zero output if there are no pairs."""
    glcm = np.asarray(glcm, dtype=np.float64)
    total = glcm.sum(axis=(-2, -1), keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        p = np.where(total > 0, glcm / np.where(total > 0, total, 1), 0.0)
    return p


def compute_asm(p):
    """Angular Second Moment: sum_i sum_j P(i, j)^2 (works on (..., L, L))."""
    return np.sum(p * p, axis=(-2, -1))


def compute_contrast(p):
    """Contrast: sum_i sum_j (i - j)^2 P(i, j)."""
    L = p.shape[-1]
    i, j = np.indices((L, L))
    return np.sum(((i - j) ** 2) * p, axis=(-2, -1))


def compute_mean(p):
    """GLCM mean: mu_x = sum_i i * P_x(i), with P_x(i) = sum_j P(i, j)."""
    L = p.shape[-1]
    px = p.sum(axis=-1)
    return np.sum(np.arange(L) * px, axis=-1)


# ---------------------------------------------------------------------------
# Moving-window GLCM
# ---------------------------------------------------------------------------

def _pad(q, window_size):
    half = window_size // 2
    return np.pad(q, half, mode="reflect")


def moving_window_glcm_naive(q, window_size, num_levels, offset=(0, 1),
                             symmetric=False, return_glcm=False):
    """Reference moving-window GLCM: one explicit GLCM per window position.

    Parameters
    ----------
    q : (H, W) int array of gray levels 0 .. L-1.

    Returns
    -------
    dict with 'ASM', 'CON', 'MEAN' texture images (H, W) and, if requested,
    'GLCM' of shape (H, W, L, L) holding the normalised local matrices.
    """
    H, W = q.shape
    padded = _pad(q, window_size)
    asm = np.zeros((H, W))
    con = np.zeros((H, W))
    mean = np.zeros((H, W))
    glcms = np.zeros((H, W, num_levels, num_levels)) if return_glcm else None
    for r in range(H):
        for c in range(W):
            patch = padded[r:r + window_size, c:c + window_size]
            p = normalize_glcm(compute_glcm(patch, num_levels, offset, symmetric))
            asm[r, c] = compute_asm(p)
            con[r, c] = compute_contrast(p)
            mean[r, c] = compute_mean(p)
            if return_glcm:
                glcms[r, c] = p
    out = {"ASM": asm, "CON": con, "MEAN": mean}
    if return_glcm:
        out["GLCM"] = glcms
    return out


def _box_sum(indicator, out_shape, start, size):
    """Sum ``indicator`` over a (size) box whose top-left corner for output
    pixel (r, c) is (r + start[0], c + start[1]), using an integral image."""
    H, W = out_shape
    bh, bw = size
    sr, sc = start
    S = np.zeros((indicator.shape[0] + 1, indicator.shape[1] + 1), dtype=np.int64)
    S[1:, 1:] = indicator.cumsum(axis=0).cumsum(axis=1)
    r0, c0 = sr, sc
    return (S[r0 + bh:r0 + bh + H, c0 + bw:c0 + bw + W]
            - S[r0:r0 + H, c0 + bw:c0 + bw + W]
            - S[r0 + bh:r0 + bh + H, c0:c0 + W]
            + S[r0:r0 + H, c0:c0 + W])


def moving_window_glcm(q, window_size, num_levels, offset=(0, 1),
                       symmetric=False, return_glcm=False):
    """Vectorised moving-window GLCM giving the same local GLCMs as the naive one.

    For each gray-level pair code k = i * L + j an indicator image marks the
    reference pixels p with (q[p], q[p + offset]) == (i, j). Box-summing that
    indicator over the valid reference region of every window yields
    GLCM_window(i, j) for all windows simultaneously. The features are
    accumulated code by code, so memory stays O(H * W) unless the full
    (H, W, L, L) stack is requested with ``return_glcm``.
    """
    H, W = q.shape
    L = num_levels
    dr, dc = offset
    padded = _pad(q, window_size)
    Hp, Wp = padded.shape

    # Reference-pixel box inside each window: rows [a_r, a_r + h_eff), cols likewise.
    h_eff = window_size - abs(dr)
    w_eff = window_size - abs(dc)
    a_r, a_c = max(0, -dr), max(0, -dc)

    asm = np.zeros((H, W))
    con = np.zeros((H, W))
    mean = np.zeros((H, W))
    glcms = np.zeros((H, W, L, L)) if return_glcm else None
    if h_eff <= 0 or w_eff <= 0:
        out = {"ASM": asm, "CON": con, "MEAN": mean}
        if return_glcm:
            out["GLCM"] = glcms
        return out

    # Pair code for every padded reference pixel whose neighbour is in bounds;
    # -1 elsewhere (those positions never fall inside a window's reference box).
    codes = np.full((Hp, Wp), -1, dtype=np.int64)
    ref_sl, nbr_sl = _pair_slices((Hp, Wp), offset)
    codes[ref_sl] = padded[ref_sl] * L + padded[nbr_sl]

    n_pairs = h_eff * w_eff * (2 if symmetric else 1)

    def counts_for(i, j):
        return _box_sum(codes == i * L + j, (H, W), (a_r, a_c), (h_eff, w_eff))

    for i in range(L):
        for j in range(L):
            if symmetric and j < i:
                continue
            c_ij = counts_for(i, j)
            if symmetric:
                c_ji = c_ij if i == j else counts_for(j, i)
                p_ij = (c_ij + c_ji) / n_pairs
                p_ji = p_ij
            else:
                p_ij = c_ij / n_pairs

            asm += p_ij ** 2
            con += (i - j) ** 2 * p_ij
            mean += i * p_ij
            if return_glcm:
                glcms[:, :, i, j] = p_ij
            if symmetric and i != j:
                asm += p_ji ** 2
                con += (i - j) ** 2 * p_ji
                mean += j * p_ji
                if return_glcm:
                    glcms[:, :, j, i] = p_ji

    out = {"ASM": asm, "CON": con, "MEAN": mean}
    if return_glcm:
        out["GLCM"] = glcms
    return out


def window_mean_direct(q, window_size):
    """Plain mean gray level of each (reflect-padded) window -- cross-check only."""
    padded = _pad(q, window_size).astype(np.int64)
    H, W = q.shape
    total = _box_sum(padded, (H, W), (0, 0), (window_size, window_size))
    return total / float(window_size * window_size)


def extract_texture_features(image, window_size, num_levels, distance=1, angle=0,
                             lo=None, hi=None, symmetric=False, method="vectorized"):
    """Quantise ``image`` and compute the ASM / CON / MEAN texture images.

    Returns a dict with keys 'quantized', 'ASM', 'CON', 'MEAN'.
    """
    q = quantize_image(image, num_levels, lo, hi)
    offset = angle_to_offset(distance, angle)
    fn = moving_window_glcm if method == "vectorized" else moving_window_glcm_naive
    feats = fn(q, window_size, num_levels, offset, symmetric)
    feats["quantized"] = q
    return feats
