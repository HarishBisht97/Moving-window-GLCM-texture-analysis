"""K-Means clustering of per-pixel [ASM, CON, MEAN] texture feature vectors."""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from config import FEATURE_NAMES, KMEANS_N_INIT, RANDOM_STATE


def build_feature_matrix(features, names=FEATURE_NAMES):
    """Stack texture images into an (H*W, n_features) matrix X = [ASM, CON, MEAN]."""
    return np.column_stack([features[n].ravel() for n in names])


def cluster_features(features, k, random_state=RANDOM_STATE, n_init=KMEANS_N_INIT,
                     names=FEATURE_NAMES):
    """Standardise the feature vectors and run K-Means.

    Clusters are relabelled 0 .. K-1 in ascending order of the MEAN coordinate
    of their centre (ties broken by CON), so a given label/colour represents a
    comparable (dark -> bright) texture class in every experiment.

    Returns a dict with
        labels       (H, W) int cluster map
        centers      (K, n_features) centres in original feature units
        centers_std  (K, n_features) centres in standardised units
        sizes        (K,) pixel count per cluster
        inertia      K-Means objective on the standardised data
    """
    shape = features[names[0]].shape
    X = build_feature_matrix(features, names)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    km = KMeans(n_clusters=k, n_init=n_init, random_state=random_state)
    raw_labels = km.fit_predict(Xs)
    centers_std = km.cluster_centers_
    centers = scaler.inverse_transform(centers_std)

    mean_idx = names.index("MEAN") if "MEAN" in names else 0
    con_idx = names.index("CON") if "CON" in names else 0
    order = np.lexsort((centers[:, con_idx], centers[:, mean_idx]))
    remap = np.empty(k, dtype=np.int64)
    remap[order] = np.arange(k)

    labels = remap[raw_labels].reshape(shape)
    return {
        "labels": labels,
        "centers": centers[order],
        "centers_std": centers_std[order],
        "sizes": np.bincount(labels.ravel(), minlength=k),
        "inertia": float(km.inertia_),
        "feature_names": list(names),
    }
