"""Synthetic benchmark generators for the three PACE escape routes."""

from __future__ import annotations

import itertools
import math

import numpy as np


def generate_clue_grid_items(
    n_items: int = 50, k_agents: int = 3, seed: int = 42
) -> list[dict]:
    if n_items < 1 or k_agents < 2:
        raise ValueError("n_items must be positive and k_agents >= 2")
    rng = np.random.default_rng(seed)
    out = []
    suspects = ["Avery", "Blake", "Casey", "Drew"]
    for index in range(n_items):
        culprit = suspects[int(rng.integers(0, len(suspects)))]
        private = [
            [
                "Clue %d excludes %s." % (j + 1, suspect)
                for j, suspect in enumerate(suspects)
                if suspect != culprit and j % k_agents == agent
            ]
            for agent in range(k_agents)
        ]
        shared = ["Decoy clue: the most visible suspect is Blake."]
        out.append(
            {
                "id": "grid_%03d" % index,
                "route": "information_partitioning",
                "gold": culprit,
                "split": [
                    {
                        "agent": i,
                        "prompt": "Find the culprit. " + " ".join(shared + clues),
                    }
                    for i, clues in enumerate(private)
                ],
                "shared": "Find the culprit. "
                + " ".join(shared + [clue for clues in private for clue in clues]),
                "private_clues": private,
            }
        )
    return out


def generate_distributed_code_items(
    n_items: int = 30, k_agents: int = 3, seed: int = 42
) -> list[dict]:
    """Distinct, seed-controlled Python tasks with complementary constraints split across three agents and executable assert tests (see pace.distributed_code)."""
    from .distributed_code import generate_items

    if n_items < 1 or k_agents != 3:
        raise ValueError("distributed code benchmark requires exactly three agents")
    return generate_items(n_items, k_agents, seed)


def evaluate_with_verifier_threshold(
    p1: float,
    tau_ic: float,
    tau_ci: float,
    epsilon_fp: float,
    epsilon_fn: float,
    t_rounds: int = 3,
) -> dict:
    if (
        not 0 <= p1 <= 1
        or min(tau_ic, tau_ci, epsilon_fp, epsilon_fn) < 0
        or max(epsilon_fp, epsilon_fn) > 1
        or t_rounds < 1
    ):
        raise ValueError("invalid verifier parameters")
    kappa = tau_ic / tau_ci if tau_ci else float("inf")
    p_star = kappa / (1 + kappa) if math.isfinite(kappa) else 1.0
    kappa_v = kappa * (1 - epsilon_fn) / max(epsilon_fp, 1e-12)
    p_star_v = kappa_v / (1 + kappa_v) if math.isfinite(kappa_v) else 1.0
    critical = kappa * ((1 - p1) / p1) * (1 - epsilon_fn) if p1 else float("inf")
    trajectory = [p1]
    for _ in range(1, t_rounds):
        current = trajectory[-1]
        trajectory.append(
            current * (1 - tau_ci * epsilon_fp)
            + (1 - current) * tau_ic * (1 - epsilon_fn)
        )
    return {
        "kappa": kappa,
        "p_star": p_star,
        "kappa_v": kappa_v,
        "p_star_v": p_star_v,
        "epsilon_fp_crit": critical,
        "trajectory": trajectory,
        "strictly_improves": epsilon_fp < critical,
    }


def select_heterogeneous_panel(
    model_item_matrix: dict[str, list[int]], k_panel: int = 3
) -> dict:
    if not model_item_matrix or k_panel < 1 or k_panel > len(model_item_matrix):
        raise ValueError("invalid model panel")
    names = list(model_item_matrix)
    length = len(model_item_matrix[names[0]])
    if any(len(model_item_matrix[name]) != length for name in names):
        raise ValueError("all model vectors must have equal length")
    accuracy = {name: float(np.mean(model_item_matrix[name])) for name in names}
    correlations = {}
    for left, right in itertools.combinations(names, 2):
        e1, e2 = (
            1 - np.asarray(model_item_matrix[left]),
            1 - np.asarray(model_item_matrix[right]),
        )
        correlations[(left, right)] = (
            float(np.corrcoef(e1, e2)[0, 1]) if np.std(e1) and np.std(e2) else 0.0
        )
    panels = []
    for panel in itertools.combinations(names, k_panel):
        pairs = [
            correlations[tuple(sorted(pair))]
            for pair in itertools.combinations(panel, 2)
        ]
        rho = float(np.mean(pairs)) if pairs else 0.0
        k_eff = k_panel / (1 + (k_panel - 1) * max(0.0, rho))
        vote = np.mean(
            np.sum([model_item_matrix[name] for name in panel], axis=0)
            >= math.ceil(k_panel / 2)
        )
        panels.append(
            {
                "models": list(panel),
                "rho_bar": rho,
                "k_eff": float(k_eff),
                "vote_accuracy": float(vote),
            }
        )
    best = max(panels, key=lambda row: (row["k_eff"], row["vote_accuracy"]))
    best_single = max(accuracy, key=accuracy.get)
    return {
        "accuracy": accuracy,
        "pairwise_error_correlation": {
            "%s|%s" % key: value for key, value in correlations.items()
        },
        "panels": panels,
        "optimal_panel": best,
        "homogeneous_baseline": {
            "models": [best_single] * k_panel,
            "accuracy": accuracy[best_single],
        },
    }
