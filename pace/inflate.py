"""Beta-binomial sampling inflation (`pace inflate`): how much does a K-sample majority vote beat one sample, from a pool of n samples per item?

Model: item i is answered correctly with probability p_i ~ Beta(alpha, beta); the n pooled samples of an item are then Binomial(n, p_i), so the per-item success counts
are beta-binomial. Fit (alpha, beta) by maximum likelihood on the pool, and predict the accuracy of a vote over K samples in closed form:

    acc(K) = sum_s BetaBinomial(s; K, alpha, beta) * [ 1(s > K/2) + 0.5 * 1(s = K/2) ]

This is the *binary* majority (correct versus not correct). A plurality vote over several wrong options that split their votes does at least as well, so for
multiple-choice tasks acc(K) is a conservative (lower) prediction of plurality-vote accuracy. Pure standard library; no numpy, no scipy.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable, Sequence

LOG_LO, LOG_HI = math.log(1e-3), math.log(1e4)


def _betaln(a: float, b: float) -> float:
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def _log_choose(n: int, k: int) -> float:
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def beta_binomial_logpmf(s: int, n: int, a: float, b: float) -> float:
    return _log_choose(n, s) + _betaln(s + a, n - s + b) - _betaln(a, b)


def log_likelihood(successes: Sequence[int], n: int, a: float, b: float) -> float:
    counts = defaultdict(int)
    for s in successes:
        counts[int(s)] += 1
    return sum(c * beta_binomial_logpmf(s, n, a, b) for s, c in counts.items())


def fit_beta_binomial(successes: Sequence[int], n: int) -> tuple[float, float]:
    """Maximum-likelihood (alpha, beta) from per-item success counts out of n samples (shrinking-grid search on the log scale, clamped to [1e-3, 1e4])."""
    if not len(successes):
        raise ValueError("no items")
    if any(not 0 <= int(s) <= n for s in successes):
        raise ValueError("success counts must lie in 0..n")
    mean = min(max(sum(successes) / (n * len(successes)), 1e-3), 1 - 1e-3)
    # start: equal-ish concentration on the log scale, then coordinate refinement
    la, lb = math.log(mean * 2.0), math.log((1 - mean) * 2.0)
    best = log_likelihood(successes, n, math.exp(la), math.exp(lb))
    step = 2.0
    for _ in range(200):
        improved = False
        for da in (-step, -step / 2, 0.0, step / 2, step):
            for db in (-step, -step / 2, 0.0, step / 2, step):
                ca, cb = min(max(la + da, LOG_LO), LOG_HI), min(max(lb + db, LOG_LO), LOG_HI)
                ll = log_likelihood(successes, n, math.exp(ca), math.exp(cb))
                if ll > best + 1e-12:
                    best, la, lb, improved = ll, ca, cb, True
        if not improved:
            step *= 0.5
            if step < 1e-6:
                break
    return math.exp(la), math.exp(lb)


def vote_accuracy(a: float, b: float, K: int, tie: float = 0.5) -> float:
    """Closed-form accuracy of a binary-majority vote over K independent samples under Beta(a, b) item difficulty (ties count `tie`)."""
    if K < 1:
        raise ValueError("K must be at least 1")
    total = 0.0
    for s in range(K + 1):
        if 2 * s > K:
            w = 1.0
        elif 2 * s == K:
            w = tie
        else:
            continue
        total += w * math.exp(beta_binomial_logpmf(s, K, a, b))
    return min(1.0, total)


def empirical_vote_accuracy(successes: Sequence[int], n: int, K: int, tie: float = 0.5) -> float:
    """Exact expected binary-majority accuracy of a vote over K of the n pooled samples (hypergeometric over the choice of the K samples), averaged over items."""
    if K > n:
        raise ValueError("K cannot exceed the pool size n")
    out = 0.0
    denom = math.comb(n, K)
    for s in successes:
        acc = 0.0
        for j in range(max(0, K - (n - s)), min(K, s) + 1):
            w = 1.0 if 2 * j > K else (tie if 2 * j == K else 0.0)
            if w:
                acc += w * math.comb(s, j) * math.comb(n - s, K - j) / denom
        out += acc
    return out / len(successes)


def successes_from_rows(rows: Iterable[dict]) -> tuple[list[int], int]:
    """Per-item success counts from rows with `item` and `correct` (one row per sample). Items with fewer samples than the most common count are dropped."""
    by = defaultdict(list)
    for r in rows:
        by[str(r["item"])].append(1 if r["correct"] in (True, 1, 1.0, "1", "true", "True") else 0)
    sizes = defaultdict(int)
    for v in by.values():
        sizes[len(v)] += 1
    n = max(sizes, key=lambda k: (sizes[k], k))
    return [sum(v) for v in by.values() if len(v) == n], n


def inflate_report(successes: Sequence[int], n: int, ks: Sequence[int], wrong_options: float | None = None) -> dict:
    a, b = fit_beta_binomial(successes, n)
    p1 = a / (a + b)
    rows = []
    for K in ks:
        row = {"K": K, "predicted": vote_accuracy(a, b, K)}
        if K <= n:
            row["pool_observed"] = empirical_vote_accuracy(successes, n, K)
        if wrong_options is not None:
            row["predicted_plurality"] = plurality_accuracy(a, b, K, wrong_options)
        row["over_single_sample"] = row["predicted"] - p1
        rows.append(row)
    return {
        "n_items": len(successes),
        "pool_size": n,
        "alpha": a,
        "beta": b,
        "concentration": a + b,
        "mean_single_sample_accuracy": p1,
        "single_sample_accuracy_observed": sum(successes) / (n * len(successes)),
        "wrong_options": wrong_options,
        "inflation": rows,
        "model": "binary majority under Beta(alpha, beta) item difficulty; conservative for plurality voting over split wrong answers",
    }


# ---------------------------------------------------------------------------------------------------------------------------------------------
# Plurality extension: wrong answers are spread over W options (uniformly), so a plurality vote can win with far fewer than K/2 correct samples.
# Given the number s of correct samples among K, the K-s wrong samples are Multinomial(K-s; uniform over W wrong options), independent of p_i.
# The vote is correct if s beats the largest wrong count; a tie with j wrong options at the maximum is credited 1/(1+j) (uniform tie-break).
# W = 1 recovers the binary majority above.
# ---------------------------------------------------------------------------------------------------------------------------------------------


def _poly_mul(x: list[float], y: list[float], deg: int) -> list[float]:
    out = [0.0] * (deg + 1)
    for i, xi in enumerate(x):
        if xi == 0.0:
            continue
        for j, yj in enumerate(y):
            if i + j > deg:
                break
            out[i + j] += xi * yj
    return out


def _wrong_wins_prob(s: int, r: int, W: int) -> float:
    """P(the s correct samples win a plurality against r wrong samples spread uniformly over W options), with uniform tie-break."""
    if r == 0:
        return 1.0 if s > 0 else 0.0
    if s == 0:
        return 0.0
    total = 0.0
    for m in range(1, r + 1):
        base = [1.0 / math.factorial(i) for i in range(m)]            # sum_{i<m} x^i / i!
        powers = [[1.0]]
        for _ in range(W):
            powers.append(_poly_mul(powers[-1], base, r))
        for j in range(1, min(W, r // m) + 1):
            rest = r - j * m
            coeff = powers[W - j][rest] if rest < len(powers[W - j]) else 0.0
            ways = math.comb(W, j) * coeff / (math.factorial(m) ** j) * math.factorial(r) / (W ** r)
            credit = 1.0 if s > m else (1.0 / (1 + j) if s == m else 0.0)
            total += ways * credit
    return min(1.0, total)


def plurality_accuracy(a: float, b: float, K: int, W: float = 1.0) -> float:
    """Closed-form plurality-vote accuracy over K samples: Beta(a, b) difficulty and wrong answers spread uniformly over W options (W real; linear in W between integers)."""
    if K < 1:
        raise ValueError("K must be at least 1")
    if W < 1:
        raise ValueError("W must be at least 1")

    def at(Wi: int) -> float:
        return sum(math.exp(beta_binomial_logpmf(s, K, a, b)) * _wrong_wins_prob(s, K - s, Wi) for s in range(K + 1))

    lo = int(math.floor(W))
    if abs(W - lo) < 1e-12:
        return min(1.0, at(lo))
    return min(1.0, (1 - (W - lo)) * at(lo) + (W - lo) * at(lo + 1))


def estimate_wrong_options(rows: Iterable[dict]) -> float | None:
    """Effective number of wrong options W = 1 / (collision probability of two wrong samples of the same item), pooled over items.
    Needs rows with item, correct and answer (a label). Returns None if no item has two wrong samples."""
    by = defaultdict(list)
    for r in rows:
        if r["correct"] in (True, 1, 1.0, "1", "true", "True"):
            continue
        by[str(r["item"])].append(str(r.get("answer", "")))
    pairs = same = 0
    for answers in by.values():
        n = len(answers)
        if n < 2:
            continue
        counts = defaultdict(int)
        for a in answers:
            counts[a] += 1
        pairs += n * (n - 1) // 2
        same += sum(c * (c - 1) // 2 for c in counts.values())
    if not pairs:
        return None
    return 1.0 / max(same / pairs, 1e-9)
