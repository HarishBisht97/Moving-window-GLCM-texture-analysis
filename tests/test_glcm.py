import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from clustering import cluster_features  # noqa: E402
from glcm import (angle_to_offset, compute_asm, compute_contrast, compute_glcm,  # noqa: E402
                  compute_mean, moving_window_glcm, moving_window_glcm_naive,
                  normalize_glcm, quantize_image)
from preprocess import smooth_image  # noqa: E402


def test_hand_checked_glcm():
    # Classic 4x4 example (Haralick / scikit-image docs), L = 4, offset (0, 1).
    patch = np.array([[0, 0, 1, 1],
                      [0, 0, 1, 1],
                      [0, 2, 2, 2],
                      [2, 2, 3, 3]])
    expected = np.array([[2, 2, 1, 0],
                         [0, 2, 0, 0],
                         [0, 0, 3, 1],
                         [0, 0, 0, 1]])
    glcm = compute_glcm(patch, 4, (0, 1))
    np.testing.assert_array_equal(glcm, expected)
    assert glcm.sum() == 4 * 3

    p = normalize_glcm(glcm)
    assert np.isclose(p.sum(), 1.0)
    assert np.isclose(compute_asm(p), (4 + 4 + 1 + 4 + 9 + 1 + 1) / 144)
    # Off-diagonal pairs: (0,1) x2 -> 1, (0,2) x1 -> 4, (2,3) x1 -> 1.
    assert np.isclose(compute_contrast(p), (2 * 1 + 1 * 4 + 1 * 1) / 12)
    px = expected.sum(axis=1) / 12
    assert np.isclose(compute_mean(p), np.sum(np.arange(4) * px))


def test_symmetric_glcm():
    patch = np.array([[0, 1], [1, 2]])
    g = compute_glcm(patch, 3, (0, 1), symmetric=True)
    np.testing.assert_array_equal(g, g.T)
    assert g.sum() == 4


def test_zero_pairs_safe():
    p = normalize_glcm(np.zeros((8, 8)))
    assert np.all(p == 0)
    q = np.random.default_rng(0).integers(0, 4, (10, 10))
    out = moving_window_glcm(q, 3, 4, offset=(0, 5))
    assert all(np.all(out[k] == 0) for k in ("ASM", "CON", "MEAN"))


def test_quantize():
    img = np.array([[0, 31, 32, 255]], dtype=float)
    np.testing.assert_array_equal(quantize_image(img, 8, 0, 256), [[0, 0, 1, 7]])
    assert quantize_image(img, 8).max() == 7
    assert np.all(quantize_image(np.full((3, 3), 5.0), 8) == 0)


@pytest.mark.parametrize("angle", [0, 45, 90, 135])
@pytest.mark.parametrize("distance", [1, 2])
@pytest.mark.parametrize("symmetric", [False, True])
def test_naive_equals_vectorized(angle, distance, symmetric):
    q = np.random.default_rng(angle + distance).integers(0, 8, (40, 40))
    off = angle_to_offset(distance, angle)
    a = moving_window_glcm_naive(q, 7, 8, off, symmetric, return_glcm=True)
    b = moving_window_glcm(q, 7, 8, off, symmetric, return_glcm=True)
    for k in ("GLCM", "ASM", "CON", "MEAN"):
        np.testing.assert_allclose(a[k], b[k], atol=1e-12)
    np.testing.assert_allclose(b["GLCM"].sum(axis=(-2, -1)), 1.0)


def test_texture_image_shape_matches_input():
    q = np.random.default_rng(1).integers(0, 8, (23, 31))
    out = moving_window_glcm(q, 7, 8)
    assert all(out[k].shape == q.shape for k in ("ASM", "CON", "MEAN"))


def test_smooth_image_matches_bruteforce():
    img = np.random.default_rng(2).random((20, 25)) * 255
    s = smooth_image(img, 7)
    p = np.pad(img, 3, mode="reflect")
    brute = np.array([[p[r:r + 7, c:c + 7].mean() for c in range(25)] for r in range(20)])
    np.testing.assert_allclose(s, brute)
    np.testing.assert_allclose(smooth_image(np.full((10, 10), 7.0), 9), 7.0)


def test_cluster_labels_ordered_by_mean():
    rng = np.random.default_rng(3)
    feats = {"ASM": rng.random((30, 30)), "CON": rng.random((30, 30)),
             "MEAN": np.repeat(np.arange(3), 300).reshape(30, 30) * 3.0 + rng.random((30, 30)) * 0.1}
    res = cluster_features(feats, 3)
    assert np.all(np.diff(res["centers"][:, 2]) > 0)
    assert res["sizes"].sum() == 900
