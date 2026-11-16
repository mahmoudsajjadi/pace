"""Constructive token budgets and split-sample frontiers."""

from __future__ import annotations

import math

import numpy as np


def compute_k_tok(
    k_agents: int,
    t_rounds: int,
    c0_prompt_tokens: float,
    l_message_tokens: float,
    topology: str = "last_round_peers",
) -> dict:
    if k_agents < 1 or t_rounds < 1:
        raise ValueError("agents and rounds must be positive")
    if topology not in {"last_round_peers", "last_round_all", "full_history_echo"}:
        raise ValueError("unknown topology: %s" % topology)
    denominator = c0_prompt_tokens + l_message_tokens
    ratio = l_message_tokens / denominator if denominator > 0 else 0.0
    base = k_agents * t_rounds
    if topology == "last_round_peers":
        coefficient = (t_rounds - 1) * k_agents * (k_agents - 1)
        k_tok = base + coefficient * ratio
    elif topology == "last_round_all":
        coefficient = (t_rounds - 1) * k_agents**2
        k_tok = base + coefficient * ratio
    else:
        coefficient = 0.5 * k_agents**2 * t_rounds * (t_rounds - 1)
        k_tok = base + coefficient * ratio

    def b_eff(budget: float) -> float:
        return float(budget) / k_tok if k_tok else float("inf")

    recommended = max(8, 1)
    while recommended < math.ceil(k_tok):
        recommended *= 2
    return {
        "k_tok": float(k_tok),
        "r": float(ratio),
        "topology": topology,
        "bounds": [float(base), float(base + coefficient)],
        "k_min": float(base),
        "k_max": float(base + coefficient),
        "b_eff": b_eff,
        "recommended_pool_size": recommended,
    }


def isotonic_pava_frontier(
    budgets: list[float], accuracies: list[float], weights: list[float] | None = None
) -> list[dict]:
    if len(budgets) != len(accuracies) or not budgets:
        raise ValueError("budgets and accuracies must have equal nonzero length")
    weights = weights or [1.0] * len(budgets)
    if len(weights) != len(budgets):
        raise ValueError("weights must match budgets")
    data = sorted(
        zip(map(float, budgets), map(float, accuracies), map(float, weights)),
        key=lambda row: row[0],
    )
    blocks = []
    for budget, accuracy, weight in data:
        blocks.append([budget, accuracy, weight, 1])
        while len(blocks) > 1 and blocks[-2][1] > blocks[-1][1]:
            right = blocks.pop()
            left = blocks.pop()
            weight_sum = left[2] + right[2]
            blocks.append(
                [
                    left[0],
                    (left[1] * left[2] + right[1] * right[2]) / weight_sum,
                    weight_sum,
                    left[3] + right[3],
                ]
            )
    fitted = []
    cursor = 0
    for budget, accuracy, weight, count in blocks:
        fitted.extend(
            {
                "budget": data[cursor + i][0],
                "accuracy": data[cursor + i][1],
                "fitted_accuracy": accuracy,
                "weight": data[cursor + i][2],
            }
            for i in range(count)
        )
        cursor += count
    return fitted


def _fold_gap(scores, tokens, mas_scores, mas_tokens, train, test):
    mas_budget = float(np.mean(mas_tokens[train]))
    candidates = [
        (k, float(np.mean(scores[train, k])))
        for k in range(scores.shape[1])
        if float(np.mean(tokens[train, k])) <= mas_budget
    ]
    if not candidates:
        k = 0
    else:
        k = max(candidates, key=lambda pair: pair[1])[0]
    return (
        float(np.mean(mas_scores[test]) - np.mean(scores[test, k])),
        int(k + 1),
        mas_budget,
    )


def split_sample_frontier_gap(
    item_pool_scores: np.ndarray,
    item_pool_tokens: np.ndarray,
    mas_item_scores: np.ndarray,
    mas_item_tokens: np.ndarray,
    seed: int = 0,
) -> dict:
    scores = np.asarray(item_pool_scores, dtype=float)
    tokens = np.asarray(item_pool_tokens, dtype=float)
    if scores.ndim != 2:
        raise ValueError("item_pool_scores must be items by candidate k")
    if tokens.ndim == 1:
        tokens = np.broadcast_to(tokens, scores.shape)
    mas_scores, mas_tokens = (
        np.asarray(mas_item_scores, dtype=float).reshape(-1),
        np.asarray(mas_item_tokens, dtype=float).reshape(-1),
    )
    n = scores.shape[0]
    if (
        tokens.shape != scores.shape
        or len(mas_scores) != n
        or len(mas_tokens) != n
        or n < 2
    ):
        raise ValueError("all arrays must align and contain at least two items")
    rng = np.random.default_rng(seed)
    order = rng.permutation(n)
    split = n // 2
    a, b = order[:split], order[split:]
    gap_a, k_a, budget_a = _fold_gap(scores, tokens, mas_scores, mas_tokens, a, b)
    gap_b, k_b, budget_b = _fold_gap(scores, tokens, mas_scores, mas_tokens, b, a)
    return {
        "gap": float((gap_a + gap_b) / 2),
        "fold_a_gap": gap_a,
        "fold_b_gap": gap_b,
        "selected_k_fold_a": k_a,
        "selected_k_fold_b": k_b,
        "budget_fold_a": budget_a,
        "budget_fold_b": budget_b,
        "n_items": n,
        "seed": seed,
    }
