"""Native numpy meta-analysis and prospective power calculations."""

from __future__ import annotations

import itertools
import math

import numpy as np


def compute_effect_sizes(
    p_mas: float, p_base: float, n_items: int, phi: float = 0.5
) -> dict:
    if n_items < 1 or not 0 <= phi <= 1 or not (0 <= p_mas <= 1 and 0 <= p_base <= 1):
        raise ValueError("invalid probabilities, sample size, or phi")
    pt_m, pt_b = (
        (p_mas * n_items + 0.5) / (n_items + 1),
        (p_base * n_items + 0.5) / (n_items + 1),
    )
    log_or = math.log((pt_m / (1 - pt_m)) / (pt_b / (1 - pt_b)))
    vm, vb = 1 / (n_items * pt_m * (1 - pt_m)), 1 / (n_items * pt_b * (1 - pt_b))
    phi_max = math.exp(-abs(log_or) / 2)
    v_log_or = vm + vb - 2 * phi * math.sqrt(vm * vb)
    v_clamped = vm + vb - 2 * min(phi, phi_max) * math.sqrt(vm * vb)
    delta = p_mas - p_base
    se_delta = math.sqrt(
        max(
            0.0,
            (
                p_mas * (1 - p_mas)
                + p_base * (1 - p_base)
                - 2 * phi * math.sqrt(p_mas * (1 - p_mas) * p_base * (1 - p_base))
            )
            / n_items,
        )
    )
    h = 2 * math.asin(math.sqrt(p_mas)) - 2 * math.asin(math.sqrt(p_base))
    return {
        "p_tilde_mas": pt_m,
        "p_tilde_base": pt_b,
        "log_or": log_or,
        "v_log_or": v_log_or,
        "phi_max": phi_max,
        "v_log_or_clamped": v_clamped,
        "delta": delta,
        "se_delta": se_delta,
        "cohen_h": h,
        "v_cohen_h": 2 * (1 - phi) / n_items,
        "phi_clamped": phi > phi_max,
    }


def shared_baseline_deff(
    m_contrasts_sharing_baseline: int, v_mas: float, v_base: float
) -> dict:
    if m_contrasts_sharing_baseline < 1 or min(v_mas, v_base) < 0:
        raise ValueError("invalid variance or block size")
    rho = v_base / (v_mas + v_base) if v_mas + v_base else 0.0
    deff = 1 + (m_contrasts_sharing_baseline - 1) * rho
    naive = (v_mas + v_base) / m_contrasts_sharing_baseline
    return {
        "rho_base": rho,
        "deff": deff,
        "naive_diagonal_variance": naive,
        "true_shared_baseline_variance": naive * deff,
    }


def build_che_covariance(
    contrasts: list[dict], rho_block: float = 0.5, block_by: str = "baseline_cell"
) -> np.ndarray:
    if not 0 <= rho_block <= 1 or block_by not in {
        "baseline_cell",
        "benchmark",
        "study",
    }:
        raise ValueError("invalid rho_block or block_by")
    keys = {
        "baseline_cell": lambda r: (
            r.get("study"),
            r.get("benchmark"),
            r.get("model"),
            r.get("category"),
        ),
        "benchmark": lambda r: (r.get("study"), r.get("benchmark")),
        "study": lambda r: (r.get("study"),),
    }[block_by]
    n = len(contrasts)
    matrix = np.zeros((n, n))
    variances = [
        float(r.get("variance", 1 / max(1, int(float(r.get("n", 1)))))) for r in contrasts
    ]
    for i in range(n):
        matrix[i, i] = variances[i]
        for j in range(i):
            if keys(contrasts[i]) == keys(contrasts[j]):
                matrix[i, j] = matrix[j, i] = rho_block * math.sqrt(
                    variances[i] * variances[j]
                )
    return matrix


def der_simonian_laird_pool(y: np.ndarray, v: np.ndarray, clusters: list[str]) -> dict:
    y, v = np.asarray(y, dtype=float), np.asarray(v, dtype=float)
    if y.ndim != 1 or len(y) != len(v) or len(y) != len(clusters) or np.any(v <= 0):
        raise ValueError("y, v, and clusters must align and v must be positive")
    w = 1 / v
    fixed = float(np.sum(w * y) / np.sum(w))
    q = float(np.sum(w * (y - fixed) ** 2))
    df = len(y) - 1
    tau2 = max(0.0, (q - df) / (np.sum(w) - np.sum(w**2) / np.sum(w))) if df else 0.0
    wr = 1 / (v + tau2)
    estimate = float(np.sum(wr * y) / np.sum(wr))
    groups = sorted(set(clusters))
    scores = {
        g: float(
            np.sum(
                wr[[i for i, c in enumerate(clusters) if c == g]]
                * (y[[i for i, c in enumerate(clusters) if c == g]] - estimate)
            )
        )
        for g in groups
    }
    sandwich = (
        sum(score**2 for score in scores.values())
        / max(1, len(groups) - 1)
        / max(np.sum(wr) ** 2, 1e-12)
    )
    se = math.sqrt(max(0.0, sandwich))
    df_sat = max(1.0, len(groups) - 1)
    ci = [estimate - 1.96 * se, estimate + 1.96 * se]
    signs = []
    if len(groups) <= 16:
        for signs_tuple in itertools.product((-1, 1), repeat=len(groups)):
            signs.append(
                abs(sum(scores[g] * sign for g, sign in zip(groups, signs_tuple)))
            )
        p_value = sum(value >= abs(sum(scores.values())) for value in signs) / len(
            signs
        )
    else:
        p_value = None
    loco = []
    for group in groups:
        mask = np.array([c != group for c in clusters])
        pooled = (
            der_simonian_laird_pool(y[mask], v[mask], list(np.asarray(clusters)[mask]))
            if mask.sum() > 1
            else None
        )
        loco.append(
            {
                "cluster": group,
                "estimate": None if pooled is None else pooled["estimate"],
            }
        )
    return {
        "estimate": estimate,
        "tau2_dl": tau2,
        "se": se,
        "df": df_sat,
        "ci95": ci,
        "prediction_interval_study": [
            estimate - 1.96 * math.sqrt(se * se + tau2),
            estimate + 1.96 * math.sqrt(se * se + tau2),
        ],
        "prediction_interval_single": [
            estimate - 1.96 * math.sqrt(se * se + tau2),
            estimate + 1.96 * math.sqrt(se * se + tau2),
        ],
        "p_value": p_value,
        "loco": loco,
        "q": q,
    }


def prospective_power_analysis(
    p_base: float,
    target_delta: float,
    n_items: int | None = None,
    target_power: float = 0.8,
    alpha: float = 0.05,
    phi: float = 0.5,
    k_shared_arms: int = 1,
) -> dict:
    if (
        not 0 < p_base < 1
        or target_delta == 0
        or not 0 < target_power < 1
        or not 0 < alpha < 1
        or k_shared_arms < 1
    ):
        raise ValueError("invalid power parameters")
    adjusted_alpha = alpha / k_shared_arms
    z_alpha, z_power = (
        1.96 if adjusted_alpha <= 0.05 else 1.645,
        0.8416 if target_power >= 0.8 else 0.5244,
    )
    variance = (
        p_base * (1 - p_base)
        + (p_base + target_delta) * (1 - p_base - target_delta)
        - 2
        * phi
        * math.sqrt(
            p_base
            * (1 - p_base)
            * (p_base + target_delta)
            * (1 - p_base - target_delta)
        )
    )
    n_min = math.ceil(((z_alpha + z_power) ** 2 * variance) / target_delta**2)
    achieved = (
        None
        if n_items is None
        else min(
            1.0,
            max(
                0.0,
                0.5
                * (
                    1
                    + math.erf(
                        (
                            abs(target_delta)
                            * math.sqrt(n_items / max(variance, 1e-12))
                            - z_alpha
                        )
                        / math.sqrt(2)
                    )
                ),
            ),
        )
    )
    mde = (
        None
        if n_items is None
        else (z_alpha + z_power) * math.sqrt(max(variance, 1e-12) / n_items)
    )
    return {
        "n_min_items": n_min,
        "achieved_power": achieved,
        "mde": mde,
        "alpha_adjusted": adjusted_alpha,
        "phi": phi,
        "n_items": n_items,
    }
