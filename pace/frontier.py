"""Self-consistency frontier and frontier gap with a paired bootstrap.

A sample pool holds, for each item, up to K independent sampled answers with token counts. For k = 1..K the expected accuracy of
plurality voting over k samples is estimated over random k-subsets (ties share credit equally). The cost of k samples is k times the
mean tokens per sample. The frontier is the nondecreasing (isotonic) fit of accuracy against tokens, interpolated linearly.

frontier gap = accuracy of a system - frontier(mean tokens the system used). A positive gap means the system sits above what
sampling alone would reach at that measured token cost. The bootstrap resamples items and recomputes everything (pool curve,
isotonic fit, interpolation, system accuracy), so the interval accounts for sampling noise in both sides.
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np


def plurality_credit(answers: Sequence[str], gold: str) -> float:
    """1 if the plurality answer equals gold; 1/m if gold is one of m tied leaders; 0 otherwise."""
    c = Counter(answers)
    top = max(c.values())
    leaders = [a for a, v in c.items() if v == top]
    return (1.0 / len(leaders)) if gold in leaders else 0.0


def item_vote_curve(answers: Sequence[str], gold: str, K: int, n_perm: int, rng: np.random.Generator) -> np.ndarray:
    """Expected plurality accuracy of k = 1..K samples for one item. Each random permutation gives nested prefixes; the value at
    k equal to the number of samples is exact (order does not matter)."""
    n = len(answers)
    if K > n:
        raise ValueError("K exceeds the number of samples for an item")
    out = np.zeros(K)
    for _ in range(n_perm):
        c: Counter = Counter()
        for k, i in enumerate(rng.permutation(n)[:K], 1):
            c[answers[i]] += 1
            top = max(c.values())
            leaders = [a for a, v in c.items() if v == top]
            out[k - 1] += (1.0 / len(leaders)) if gold in leaders else 0.0
    return out / n_perm


def pav_increasing(y: np.ndarray, w: Optional[np.ndarray] = None) -> np.ndarray:
    """Weighted pool-adjacent-violators: the nondecreasing least-squares fit to y."""
    y = np.asarray(y, dtype=float)
    w = np.ones_like(y) if w is None else np.asarray(w, dtype=float)
    blocks: List[List[float]] = []  # [value, weight, count]
    for yi, wi in zip(y, w):
        blocks.append([yi, wi, 1])
        while len(blocks) > 1 and blocks[-2][0] > blocks[-1][0]:
            v2, w2, c2 = blocks.pop()
            v1, w1, c1 = blocks.pop()
            blocks.append([(v1 * w1 + v2 * w2) / (w1 + w2), w1 + w2, c1 + c2])
    return np.concatenate([[b[0]] * int(b[2]) for b in blocks])


def envelope_increasing(y: np.ndarray) -> np.ndarray:
    """In-sample nondecreasing monotone envelope: f^+_k = max_{j <= k} y_j."""
    arr = np.asarray(y, dtype=float)
    if arr.size == 0:
        return arr.copy()
    return np.maximum.accumulate(arr)


def crossfit_frontier(
    acc: np.ndarray,
    tok: np.ndarray,
    t: float,
    n_splits: int = 200,
    seed: int = 0,
) -> Tuple[float, str]:
    """Two-fold item cross-fitted lower frontier estimator f^-(C) at token budget t.

    In each random split into folds S_1, S_2, fold 1 selects k_hat_1 = argmax_{k: k * c_bar_1 <= t} a_hat_1(k)
    and evaluates a_hat_2(k_hat_1) on fold 2, averaged symmetrically across both directions and n_splits splits.
    Returns (value, status) with status in {'inside', 'below range', 'beyond range'}.
    """
    acc_arr = np.asarray(acc, dtype=float)
    tok_arr = np.asarray(tok, dtype=float)
    if acc_arr.ndim != 2 or acc_arr.shape[0] < 1 or acc_arr.shape[1] < 1:
        raise ValueError("acc must be a non-empty 2D array (n_items, K)")
    if tok_arr.shape != (acc_arr.shape[0],):
        raise ValueError("tok must be a 1D array aligned with acc rows")
    if n_splits < 1:
        raise ValueError("n_splits must be >= 1")

    n, K = acc_arr.shape
    c_1 = float(tok_arr.mean())
    c_max = float(K * c_1)
    if t < c_1:
        return float(acc_arr[:, 0].mean()), "below range"
    status = "beyond range" if t > c_max else "inside"

    ks = np.arange(1, K + 1, dtype=float)
    if n < 2:
        feas = np.flatnonzero(ks * c_1 <= t)
        k_best = int(feas[np.argmax(acc_arr[0, feas])]) if len(feas) else 0
        return float(acc_arr[0, k_best]), status

    mid = n // 2
    rng = np.random.default_rng(seed)
    total = 0.0
    done = 0
    while done < n_splits:
        b = min(500, n_splits - done)
        perms = np.argsort(rng.random((b, n)), axis=1)
        f1 = perms[:, :mid]
        f2 = perms[:, mid:]
        a1 = acc_arr[f1].mean(axis=1)
        a2 = acc_arr[f2].mean(axis=1)
        c1 = tok_arr[f1].mean(axis=1)
        c2 = tok_arr[f2].mean(axis=1)
        feas1 = (c1[:, None] * ks[None, :]) <= t
        feas2 = (c2[:, None] * ks[None, :]) <= t
        m1 = np.where(feas1, a1, -np.inf)
        m2 = np.where(feas2, a2, -np.inf)
        k1 = np.where(feas1.any(axis=1), np.argmax(m1, axis=1), 0)
        k2 = np.where(feas2.any(axis=1), np.argmax(m2, axis=1), 0)
        row_ix = np.arange(b)
        total += float(0.5 * (a2[row_ix, k1] + a1[row_ix, k2]).sum())
        done += b
    return float(total / n_splits), status


def frontier_at(
    tokens_k: np.ndarray,
    acc_k: np.ndarray,
    t: float,
    estimator: str = "isotonic",
) -> Tuple[float, str]:
    """Frontier interpolated at t. Returns (value, status) with status in {'inside', 'below range', 'beyond range'}."""
    if estimator == "isotonic":
        fit = pav_increasing(acc_k)
    elif estimator == "envelope":
        fit = envelope_increasing(acc_k)
    else:
        raise ValueError(f"unsupported curve estimator: {estimator!r}")
    if t < tokens_k[0]:
        return float(fit[0]), "below range"
    if t > tokens_k[-1]:
        return float(fit[-1]), "beyond range"
    return float(np.interp(t, tokens_k, fit)), "inside"


class Pool:
    """Per-item sampled answers and token counts. items: id -> dict(gold, answers[list[str]], tokens[list[float]])."""

    def __init__(self, items: Dict[str, dict], K: Optional[int] = None):
        self.items = items
        self.K = K or min(len(v["answers"]) for v in items.values())
        if self.K < 1:
            raise ValueError("pool has an item with no samples")

    def curves(self, n_perm: int = 100, seed: int = 0) -> Tuple[List[str], np.ndarray, np.ndarray]:
        """Return (item ids, acc[item, k], tokens_per_sample[item]) with k = 1..K."""
        rng = np.random.default_rng(seed)
        ids = sorted(self.items)
        acc = np.zeros((len(ids), self.K))
        tok = np.zeros(len(ids))
        for i, it in enumerate(ids):
            v = self.items[it]
            acc[i] = item_vote_curve(v["answers"][: len(v["answers"])], v["gold"], self.K, n_perm, rng)
            tok[i] = float(np.mean(v["tokens"]))
        return ids, acc, tok


def frontier_curve(acc: np.ndarray, tok: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Population-level points: tokens_k = k * mean tokens per sample, acc_k = mean over items."""
    K = acc.shape[1]
    return np.arange(1, K + 1) * float(tok.mean()), acc.mean(axis=0)


def frontier_gap(
    acc: np.ndarray,
    tok: np.ndarray,
    sys_correct: np.ndarray,
    sys_tokens: np.ndarray,
    n_boot: int = 2000,
    seed: int = 0,
    alpha: float = 0.05,
    estimator: str = "isotonic",
    claim_direction: str = "auto",
    n_splits: int = 200,
) -> dict:
    """Paired bootstrap of (system accuracy - frontier at the system's mean tokens). Arrays are aligned by item."""
    if estimator not in {"isotonic", "envelope", "crossfit", "directional"}:
        raise ValueError(f"unknown estimator: {estimator!r}")
    if claim_direction not in {"auto", "positive", "nonpositive"}:
        raise ValueError(f"unknown claim_direction: {claim_direction!r}")
    n = acc.shape[0]
    if not (len(sys_correct) == len(sys_tokens) == n):
        raise ValueError("pool and system arrays must cover the same items")

    tk, ak = frontier_curve(acc, tok)
    sys_acc = float(sys_correct.mean())
    sys_tok = float(sys_tokens.mean())

    if estimator == "isotonic":
        f0, status = frontier_at(tk, ak, sys_tok, estimator="isotonic")
        est = float(sys_acc - f0)
        rng = np.random.default_rng(seed)
        gaps = np.empty(n_boot)
        for b in range(n_boot):
            ix = rng.integers(0, n, n)
            tkb, akb = frontier_curve(acc[ix], tok[ix])
            fb, _ = frontier_at(tkb, akb, float(sys_tokens[ix].mean()), estimator="isotonic")
            gaps[b] = sys_correct[ix].mean() - fb
        lo, hi = np.quantile(gaps, [alpha / 2, 1 - alpha / 2])
        return {
            "gap": est,
            "ci_low": float(lo),
            "ci_high": float(hi),
            "p_gap_le_0": float((np.sum(gaps <= 0) + 1) / (n_boot + 1)),
            "frontier_at_system_tokens": f0,
            "range_status": status,
            "system_accuracy": sys_acc,
            "system_mean_tokens": sys_tok,
            "n_items": int(n),
            "n_boot": n_boot,
        }

    if estimator in {"envelope", "crossfit"}:
        if estimator == "envelope":
            f0, status = frontier_at(tk, ak, sys_tok, estimator="envelope")
        else:
            f0, status = crossfit_frontier(acc, tok, sys_tok, n_splits=n_splits, seed=seed)
        est = float(sys_acc - f0)
        rng = np.random.default_rng(seed)
        gaps = np.empty(n_boot)
        for b in range(n_boot):
            ix = rng.integers(0, n, n)
            if estimator == "envelope":
                tkb, akb = frontier_curve(acc[ix], tok[ix])
                fb, _ = frontier_at(tkb, akb, float(sys_tokens[ix].mean()), estimator="envelope")
            else:
                fb, _ = crossfit_frontier(acc[ix], tok[ix], float(sys_tokens[ix].mean()), n_splits=n_splits, seed=seed + 1 + b)
            gaps[b] = sys_correct[ix].mean() - fb
        lo, hi = np.quantile(gaps, [alpha / 2, 1 - alpha / 2])
        p_le = float((np.sum(gaps <= 0) + 1) / (n_boot + 1))
        p_ge = float((np.sum(gaps >= 0) + 1) / (n_boot + 1))
        return {
            "gap": est,
            "ci_low": float(lo),
            "ci_high": float(hi),
            "p_gap_le_0": p_le,
            "p_two_sided": float(min(1.0, 2.0 * min(p_le, p_ge))),
            "frontier_at_system_tokens": f0,
            "range_status": status,
            "system_accuracy": sys_acc,
            "system_mean_tokens": sys_tok,
            "n_items": int(n),
            "n_boot": n_boot,
            "estimator": estimator,
        }

    # estimator == "directional": compute both crossfit (lower bound) and envelope (upper bound)
    f_cf, status_cf = crossfit_frontier(acc, tok, sys_tok, n_splits=n_splits, seed=seed)
    f_env, status_env = frontier_at(tk, ak, sys_tok, estimator="envelope")
    f_iso, _ = frontier_at(tk, ak, sys_tok, estimator="isotonic")
    gap_cf = float(sys_acc - f_cf)
    gap_env = float(sys_acc - f_env)
    if claim_direction == "positive":
        selected = "envelope"
    elif claim_direction == "nonpositive":
        selected = "crossfit"
    else:
        selected = "envelope" if sys_acc > f_iso else "crossfit"

    f0 = f_env if selected == "envelope" else f_cf
    status = status_env if selected == "envelope" else status_cf
    est = gap_env if selected == "envelope" else gap_cf

    rng = np.random.default_rng(seed)
    gaps_cf = np.empty(n_boot)
    gaps_env = np.empty(n_boot)
    for b in range(n_boot):
        ix = rng.integers(0, n, n)
        tb = float(sys_tokens[ix].mean())
        ab = float(sys_correct[ix].mean())
        tkb, akb = frontier_curve(acc[ix], tok[ix])
        fb_env, _ = frontier_at(tkb, akb, tb, estimator="envelope")
        fb_cf, _ = crossfit_frontier(acc[ix], tok[ix], tb, n_splits=n_splits, seed=seed + 1 + b)
        gaps_env[b] = ab - fb_env
        gaps_cf[b] = ab - fb_cf

    gaps = gaps_env if selected == "envelope" else gaps_cf
    lo, hi = np.quantile(gaps, [alpha / 2, 1 - alpha / 2])
    lo_cf, hi_cf = np.quantile(gaps_cf, [alpha / 2, 1 - alpha / 2])
    lo_env, hi_env = np.quantile(gaps_env, [alpha / 2, 1 - alpha / 2])
    p_le_sel = float((np.sum(gaps <= 0) + 1) / (n_boot + 1))
    p_ge_sel = float((np.sum(gaps >= 0) + 1) / (n_boot + 1))
    p_le_cf = float((np.sum(gaps_cf <= 0) + 1) / (n_boot + 1))
    p_ge_cf = float((np.sum(gaps_cf >= 0) + 1) / (n_boot + 1))
    p_le_env = float((np.sum(gaps_env <= 0) + 1) / (n_boot + 1))
    p_ge_env = float((np.sum(gaps_env >= 0) + 1) / (n_boot + 1))
    return {
        "gap": est,
        "ci_low": float(lo),
        "ci_high": float(hi),
        "p_gap_le_0": p_le_sel,
        "p_two_sided": float(min(1.0, 2.0 * min(p_le_sel, p_ge_sel))),
        "frontier_at_system_tokens": float(f0),
        "range_status": status,
        "system_accuracy": sys_acc,
        "system_mean_tokens": sys_tok,
        "n_items": int(n),
        "n_boot": n_boot,
        "estimator": "directional",
        "claim_direction": claim_direction,
        "selected_estimator": selected,
        "frontier_crossfit": float(f_cf),
        "gap_crossfit": gap_cf,
        "crossfit_ci_low": float(lo_cf),
        "crossfit_ci_high": float(hi_cf),
        "crossfit_p_gap_le_0": p_le_cf,
        "crossfit_p_two_sided": float(min(1.0, 2.0 * min(p_le_cf, p_ge_cf))),
        "frontier_envelope": float(f_env),
        "gap_envelope": gap_env,
        "envelope_ci_low": float(lo_env),
        "envelope_ci_high": float(hi_env),
        "envelope_p_gap_le_0": p_le_env,
        "envelope_p_two_sided": float(min(1.0, 2.0 * min(p_le_env, p_ge_env))),
        "frontier_isotonic": float(f_iso),
        "gap_isotonic": float(sys_acc - f_iso),
    }
