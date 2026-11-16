"""Deterministic Monte Carlo generators for PACE theory diagnostics."""

from __future__ import annotations

import numpy as np


def _validate_probability(value: float, name: str) -> None:
    if not 0 <= value <= 1:
        raise ValueError("%s must be in [0, 1]" % name)


def _majority(values: np.ndarray, n_choices: int) -> int:
    counts = np.bincount(values.astype(int), minlength=n_choices)
    leaders = np.flatnonzero(counts == counts.max())
    return int(leaders[0])


def simulate_correlated_voting(
    n_items: int,
    k_agents: int,
    p_mean: float,
    rho_peer: float,
    n_choices: int = 2,
    seed: int = 0,
) -> dict:
    """Simulate item difficulty as a beta latent variable and correlated answers."""
    if n_items < 1 or k_agents < 1 or n_choices < 2:
        raise ValueError(
            "n_items, k_agents, and n_choices must be positive; n_choices >= 2"
        )
    _validate_probability(p_mean, "p_mean")
    _validate_probability(rho_peer, "rho_peer")
    rng = np.random.default_rng(seed)
    concentration = max(2.0, 1.0 / max(rho_peer, 1e-9) - 1.0) if rho_peer else 1e9
    alpha, beta = (
        max(1e-6, p_mean * concentration),
        max(1e-6, (1 - p_mean) * concentration),
    )
    truth = rng.integers(0, n_choices, n_items)
    answers = np.empty((n_items, k_agents), dtype=int)
    for i in range(n_items):
        difficulty = float(rng.beta(alpha, beta))
        for agent in range(k_agents):
            answers[i, agent] = (
                truth[i]
                if rng.random() < difficulty
                else int(
                    rng.integers(0, n_choices - 1)
                    + (rng.integers(0, n_choices) >= truth[i])
                )
                % n_choices
            )
    correct = answers == truth[:, None]
    p1 = float(correct.mean())
    votes = np.array([_majority(row, n_choices) for row in answers])
    p_vote = float(np.mean(votes == truth))
    correlations = []
    if k_agents > 1:
        correlations = np.corrcoef(correct.T)[np.triu_indices(k_agents, 1)].tolist()
    rho_total = float(np.nanmean(correlations)) if correlations else 0.0
    k_eff = k_agents / (1 + (k_agents - 1) * rho_peer)
    hoeffding = (
        max(0.0, 1.0 - np.exp(-2 * k_eff * max(p_mean - 0.5, 0) ** 2))
        if n_choices == 2
        else max(0.0, 1.0 - np.exp(-2 * k_eff * max(p_mean - 1 / n_choices, 0) ** 2))
    )
    return {
        "p1": p1,
        "p_vote": p_vote,
        "rho_total": rho_total,
        "rho_peer": rho_peer,
        "k_eff": k_eff,
        "hoeffding_lower_bound": hoeffding,
        "answers": answers.tolist(),
        "truth": truth.tolist(),
    }


def simulate_debate_dynamics(
    n_items: int,
    k_agents: int,
    t_rounds: int,
    p1: float,
    regime: str = "constant",
    params: dict | None = None,
    n_replicates: int = 1,
    verifier_fp: float | None = None,
    verifier_fn: float | None = None,
    seed: int = 0,
) -> list[dict]:
    """Generate scored, round-indexed transcripts under a peer-influence regime."""
    if min(n_items, k_agents, t_rounds, n_replicates) < 1:
        raise ValueError("counts must be positive")
    _validate_probability(p1, "p1")
    if regime not in {"constant", "linear_martingale", "convex_amplification"}:
        raise ValueError("unknown regime: %s" % regime)
    params = params or {"a": 0.25, "b": 0.15}
    a, b = float(params.get("a", 0.25)), float(params.get("b", 0.15))
    if min(a, b) < 0 or max(a, b) > 1:
        raise ValueError("regime rates must be in [0, 1]")
    if verifier_fp is not None or verifier_fn is not None:
        _validate_probability(float(verifier_fp or 0), "verifier_fp")
        _validate_probability(float(verifier_fn or 0), "verifier_fn")
    rng = np.random.default_rng(seed)
    rows = []
    for item_index in range(n_items):
        for replicate in range(n_replicates):
            states = rng.random(k_agents) < p1
            item = (
                "item_%03d#rep%d" % (item_index, replicate)
                if n_replicates > 1
                else "item_%03d" % item_index
            )
            for round_num in range(1, t_rounds + 1):
                for agent in range(k_agents):
                    prompt = 100 + (round_num - 1) * k_agents * 20
                    rows.append(
                        {
                            "item": item,
                            "replicate": replicate,
                            "agent": "agent_%d" % agent,
                            "round": round_num,
                            "correct": bool(states[agent]),
                            "answer": "A" if states[agent] else "B",
                            "prompt_tokens": prompt,
                            "completion_tokens": 20,
                        }
                    )
                if round_num == t_rounds:
                    continue
                previous = states.copy()
                correct_peers = int(previous.sum())
                for agent in range(k_agents):
                    x = (
                        (correct_peers - int(previous[agent])) / max(1, k_agents - 1)
                        if previous[agent]
                        else (k_agents - 1 - correct_peers) / max(1, k_agents - 1)
                    )
                    power = (
                        0
                        if regime == "constant"
                        else 1
                        if regime == "linear_martingale"
                        else 2
                    )
                    rate = (a if not previous[agent] else b) * (
                        x**power if power else 1
                    )
                    if rng.random() < rate:
                        is_improvement = not previous[agent]
                        if (
                            verifier_fn is not None
                            and is_improvement
                            and rng.random() < verifier_fn
                        ):
                            continue
                        if (
                            verifier_fp is not None
                            and not is_improvement
                            and rng.random() < verifier_fp
                        ):
                            continue
                        states[agent] = not states[agent]
    return rows


def simulate_scaffolding_scaling_curve(
    budgets: list[float],
    k_agents: int,
    t_rounds: int,
    c0: float,
    l_msg: float,
    b_half: float = 500.0,
    p_min: float = 0.25,
    p_max: float = 0.85,
) -> list[dict]:
    """Map total budgets to crowded MAS and SAS effective-thinking curves."""
    if min(k_agents, t_rounds) < 1 or b_half <= 0 or p_max < p_min:
        raise ValueError("invalid scaling parameters")
    out = []
    cost = (
        k_agents * t_rounds * c0 + 0.5 * k_agents**2 * t_rounds * (t_rounds - 1) * l_msg
    )
    for budget in budgets:
        b_eff = max(0.0, (float(budget) - cost) / (k_agents * t_rounds))
        sas = max(0.0, float(budget) - c0)
        hill = lambda b: p_min + (p_max - p_min) * b / (b + b_half)
        out.append(
            {
                "budget": float(budget),
                "c_total": cost,
                "b_eff": b_eff,
                "b_eff_sas": sas,
                "p_mas": hill(b_eff),
                "p_sas": hill(sas),
            }
        )
    return out
