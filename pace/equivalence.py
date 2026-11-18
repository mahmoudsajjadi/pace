"""Small CPU helpers for the revision cells: paired TOST equivalence (Cell M3) and the Route III error-decorrelation summary (Cell E3). Standard library plus numpy.

tost_paired(x, y, margin=0.03, alpha=0.05): two one-sided tests that the mean paired difference x - y lies inside (-margin, +margin), normal approximation on the paired differences.
Equivalent at level alpha when BOTH one-sided p-values are below alpha (the 1 - 2 alpha confidence interval lies inside the margin). Per-item 0/1 or real-valued vectors of equal length.

route3_summary(correct): correct[model][j] is a list over items of 0/1 outcomes of the j-th independent sample of that model (same items, same order). Returns the within-model intraclass
correlation of correctness among K samples of one model (rho_hom, averaged over models), the correlation among one sample from each model (rho_het, averaged over sample indices), and the
plurality-free "any correct" and majority accuracy of a homogeneous versus a heterogeneous K-ensemble. Route III predicts rho_het < rho_hom (cross-model error decorrelation); this is a
descriptive diagnostic, not a significance test.
"""

from __future__ import annotations

import math
from typing import Dict, Sequence

import numpy as np


def _norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def tost_paired(x: Sequence[float], y: Sequence[float], margin: float = 0.03, alpha: float = 0.05) -> dict:
    a, b = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if a.shape != b.shape or a.ndim != 1 or len(a) < 3:
        raise ValueError("x and y must be equal-length vectors with at least 3 items")
    if margin <= 0:
        raise ValueError("margin must be positive")
    d = a - b
    n = len(d)
    mean = float(d.mean())
    se = float(d.std(ddof=1) / math.sqrt(n))
    if se == 0.0:
        p_lo = 0.0 if mean > -margin else 1.0
        p_hi = 0.0 if mean < margin else 1.0
    else:
        p_lo = 1.0 - _norm_cdf((mean + margin) / se)      # H0: diff <= -margin
        p_hi = _norm_cdf((mean - margin) / se)            # H0: diff >= +margin
    z = 1.6448536269514722 if abs(alpha - 0.05) < 1e-12 else _inv_norm(1 - alpha)
    return {"n": n, "mean_diff": mean, "se": se, "margin": margin, "alpha": alpha, "ci_low": mean - z * se, "ci_high": mean + z * se,
            "p_lower": p_lo, "p_upper": p_hi, "p_tost": max(p_lo, p_hi), "equivalent": bool(max(p_lo, p_hi) < alpha)}


def _inv_norm(p: float) -> float:
    lo, hi = -10.0, 10.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if _norm_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _icc(Z: np.ndarray):
    n, k = Z.shape
    if n < 2 or k < 2:
        return None
    m = Z.mean(axis=1)
    g = Z.mean()
    msb = k * np.sum((m - g) ** 2) / (n - 1)
    msw = np.sum((Z - m[:, None]) ** 2) / (n * (k - 1))
    den = msb + (k - 1) * msw
    return None if den == 0 else float((msb - msw) / den)


def route3_summary(correct: Dict[str, Sequence[Sequence[int]]]) -> dict:
    models = sorted(correct)
    if len(models) < 2:
        raise ValueError("Route III needs at least two models")
    K = min(len(correct[m]) for m in models)
    arr = {m: np.asarray([correct[m][j] for j in range(K)], dtype=float).T for m in models}      # items x samples
    n = arr[models[0]].shape[0]
    if any(a.shape[0] != n for a in arr.values()):
        raise ValueError("all models must cover the same items")
    hom = [_icc(arr[m][:, :K]) for m in models]
    het = []
    for j in range(K):
        Z = np.column_stack([arr[m][:, j] for m in models])
        het.append(_icc(Z))
    hom_v = [v for v in hom if v is not None]
    het_v = [v for v in het if v is not None]
    # K-ensemble accuracies: homogeneous = the K samples of one model (averaged over models); heterogeneous = one sample per model, K = number of models
    kk = min(K, len(models))
    hom_major = float(np.mean([(arr[m][:, :kk].mean(axis=1) > 0.5).mean() + 0.5 * (arr[m][:, :kk].mean(axis=1) == 0.5).mean() for m in models]))
    het_cols = np.column_stack([arr[m][:, 0] for m in models])[:, :kk]
    het_major = float((het_cols.mean(axis=1) > 0.5).mean() + 0.5 * (het_cols.mean(axis=1) == 0.5).mean())
    return {"n_items": n, "models": models, "samples_per_model": K, "rho_hom": float(np.mean(hom_v)) if hom_v else None, "rho_het": float(np.mean(het_v)) if het_v else None,
            "rho_het_lt_rho_hom": (float(np.mean(het_v)) < float(np.mean(hom_v))) if hom_v and het_v else None,
            "majority_acc_homogeneous": hom_major, "majority_acc_heterogeneous": het_major, "model_accuracy": {m: float(arr[m].mean()) for m in models}}
