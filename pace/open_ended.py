"""Noncommunicating open-ended sample aggregation utilities."""

from __future__ import annotations

import difflib
import math
import re
from collections import Counter

import numpy as np


def _tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_]+", text.lower())


def _features(text: str, metric: str, n: int) -> Counter:
    source = text if metric == "ngram_cosine" else " ".join(_tokens(text))
    return Counter(source[i : i + n] for i in range(max(0, len(source) - n + 1)))


def similarity_matrix(
    candidates: list[str], metric: str = "ngram_cosine", n: int = 3
) -> np.ndarray:
    if (
        metric
        not in {"ngram_cosine", "token_jaccard", "sequence_ratio", "code_structural"}
        or n < 1
    ):
        raise ValueError("unsupported metric or n")
    size = len(candidates)
    matrix = np.eye(size)
    for i in range(size):
        for j in range(i):
            if metric == "sequence_ratio":
                score = difflib.SequenceMatcher(
                    None, candidates[i], candidates[j]
                ).ratio()
            elif metric == "token_jaccard":
                left, right = set(_tokens(candidates[i])), set(_tokens(candidates[j]))
                score = len(left & right) / len(left | right) if left | right else 1.0
            else:
                left, right = (
                    _features(candidates[i], metric, n),
                    _features(candidates[j], metric, n),
                )
                if metric == "code_structural":
                    left = Counter(_tokens(candidates[i]) + candidates[i].splitlines())
                    right = Counter(_tokens(candidates[j]) + candidates[j].splitlines())
                dot = sum(left[k] * right[k] for k in set(left) | set(right))
                denom = math.sqrt(
                    sum(v * v for v in left.values())
                    * sum(v * v for v in right.values())
                )
                score = dot / denom if denom else 0.0
            matrix[i, j] = matrix[j, i] = score
    return matrix


def mbr_centroid_select(
    candidates: list[str],
    metric: str = "ngram_cosine",
    token_costs: list[float] | None = None,
) -> dict:
    if not candidates:
        raise ValueError("candidates cannot be empty")
    if token_costs is not None and len(token_costs) != len(candidates):
        raise ValueError("token_costs must match candidates")
    matrix = similarity_matrix(candidates, metric)
    scores = (matrix.sum(axis=1) - 1) / max(1, len(candidates) - 1)
    index = int(np.argmax(scores))
    off_diag = (matrix.sum() - len(candidates)) / max(
        1, len(candidates) * (len(candidates) - 1)
    )
    return {
        "index": index,
        "selected": candidates[index],
        "consensus_score": float(scores[index]),
        "diversity_dispersion": float(1 - off_diag),
        "total_token_cost": float(sum(token_costs)) if token_costs else None,
        "similarity": matrix.tolist(),
    }


def unbiased_pass_at_k_frontier(
    n_total_samples: int,
    c_correct_samples: int,
    k_values: list[int],
    mean_tokens_per_sample: float,
) -> list[dict]:
    if (
        not 0 <= c_correct_samples <= n_total_samples
        or n_total_samples < 1
        or mean_tokens_per_sample < 0
    ):
        raise ValueError("invalid sample counts or token cost")
    out = []
    for k in k_values:
        if not 1 <= k <= n_total_samples:
            raise ValueError("k must be in [1, n_total_samples]")
        bad = (
            math.comb(n_total_samples - c_correct_samples, k)
            if n_total_samples - c_correct_samples >= k
            else 0
        )
        out.append(
            {
                "k": k,
                "pass_at_k": 1 - bad / math.comb(n_total_samples, k),
                "token_budget": k * mean_tokens_per_sample,
                "verifier_calls": k,
            }
        )
    return out
