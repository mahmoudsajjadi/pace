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
from collections.abc import Sequence

import numpy as np


def plurality_credit(answers: Sequence[str], gold: str) -> float:
    """1 if the plurality answer equals gold; 1/m if gold is one of m tied leaders; 0 otherwise."""
    c = Counter(answer for answer in answers if answer != "")
    if not c:
        return 0.0
    top = max(c.values())
    leaders = [a for a, v in c.items() if v == top]
    return (1.0 / len(leaders)) if gold in leaders else 0.0


def item_vote_curve(
    answers: Sequence[str], gold: str, K: int, n_perm: int, rng: np.random.Generator
) -> np.ndarray:
    """Expected plurality accuracy of k = 1..K samples for one item. Each random permutation gives nested prefixes; the value at
    k equal to the number of samples is exact (order does not matter)."""
    n = len(answers)
    if K > n:
        raise ValueError("K exceeds the number of samples for an item")
    out = np.zeros(K)
    for _ in range(n_perm):
        c: Counter = Counter()
        for k, i in enumerate(rng.permutation(n)[:K], 1):
            if answers[i] != "":
                c[answers[i]] += 1
            if not c:
                continue
            top = max(c.values())
            leaders = [a for a, v in c.items() if v == top]
            out[k - 1] += (1.0 / len(leaders)) if gold in leaders else 0.0
    return out / n_perm


def pav_increasing(y: np.ndarray, w: np.ndarray | None = None) -> np.ndarray:
    """Weighted pool-adjacent-violators: the nondecreasing least-squares fit to y."""
    y = np.asarray(y, dtype=float)
    w = np.ones_like(y) if w is None else np.asarray(w, dtype=float)
    blocks: list[list[float]] = []  # [value, weight, count]
    for yi, wi in zip(y, w):
        blocks.append([yi, wi, 1])
        while len(blocks) > 1 and blocks[-2][0] > blocks[-1][0]:
            v2, w2, c2 = blocks.pop()
            v1, w1, c1 = blocks.pop()
            blocks.append([(v1 * w1 + v2 * w2) / (w1 + w2), w1 + w2, c1 + c2])
    return np.concatenate([[b[0]] * int(b[2]) for b in blocks])


def frontier_at(tokens_k: np.ndarray, acc_k: np.ndarray, t: float) -> tuple[float, str]:
    """Isotonic frontier interpolated at t. Returns (value, status) with status in {'inside', 'below range', 'beyond range'}."""
    fit = pav_increasing(acc_k)
    if t < tokens_k[0]:
        return float(fit[0]), "below range"
    if t > tokens_k[-1]:
        return float(fit[-1]), "beyond range"
    return float(np.interp(t, tokens_k, fit)), "inside"


class Pool:
    """Per-item sampled answers and token counts. items: id -> dict(gold, answers[list[str]], tokens[list[float]])."""

    def __init__(self, items: dict[str, dict], K: int | None = None):
        self.items = items
        self.K = K or min(len(v["answers"]) for v in items.values())
        if self.K < 1:
            raise ValueError("pool has an item with no samples")

    def curves(
        self, n_perm: int = 100, seed: int = 0
    ) -> tuple[list[str], np.ndarray, np.ndarray]:
        """Return (item ids, acc[item, k], tokens_per_sample[item]) with k = 1..K."""
        rng = np.random.default_rng(seed)
        ids = sorted(self.items)
        acc = np.zeros((len(ids), self.K))
        tok = np.zeros(len(ids))
        for i, it in enumerate(ids):
            v = self.items[it]
            acc[i] = item_vote_curve(
                v["answers"][: len(v["answers"])], v["gold"], self.K, n_perm, rng
            )
            tok[i] = float(np.mean(v["tokens"]))
        return ids, acc, tok


def frontier_curve(acc: np.ndarray, tok: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
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
) -> dict:
    """Paired bootstrap of (system accuracy - frontier at the system's mean tokens). Arrays are aligned by item."""
    n = acc.shape[0]
    if not (len(sys_correct) == len(sys_tokens) == n):
        raise ValueError("pool and system arrays must cover the same items")
    tk, ak = frontier_curve(acc, tok)
    f0, status = frontier_at(tk, ak, float(sys_tokens.mean()))
    est = float(sys_correct.mean() - f0)
    rng = np.random.default_rng(seed)
    gaps = np.empty(n_boot)
    for b in range(n_boot):
        ix = rng.integers(0, n, n)
        tkb, akb = frontier_curve(acc[ix], tok[ix])
        fb, _ = frontier_at(tkb, akb, float(sys_tokens[ix].mean()))
        gaps[b] = sys_correct[ix].mean() - fb
    lo, hi = np.quantile(gaps, [alpha / 2, 1 - alpha / 2])
    return {
        "gap": est,
        "ci_low": float(lo),
        "ci_high": float(hi),
        "p_gap_le_0": float((np.sum(gaps <= 0) + 1) / (n_boot + 1)),
        "frontier_at_system_tokens": f0,
        "range_status": status,
        "system_accuracy": float(sys_correct.mean()),
        "system_mean_tokens": float(sys_tokens.mean()),
        "n_items": int(n),
        "n_boot": n_boot,
    }
