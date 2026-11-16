"""Peer-influence estimators for portable PACE debate logs."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np


def flow_identity_check(
    wrong_r0: int, right_r0: int, wrong_to_right: int, right_to_wrong: int
) -> dict:
    w, r, fic, fci = map(float, (wrong_r0, right_r0, wrong_to_right, right_to_wrong))
    total = w + r
    p1 = r / total if total else None
    tau_ic = fic / w if w else 0.0
    tau_ci = fci / r if r else 0.0
    denom = fic * r + fci * w
    p_star = (tau_ic / (tau_ic + tau_ci)) if tau_ic + tau_ci else None
    lhs = (p_star - p1) if p_star is not None and p1 is not None else None
    rhs = (r * w * (fic - fci) / (denom * total)) if denom and total else None
    gap = abs(lhs - rhs) if lhs is not None and rhs is not None else None
    return {
        "p1": p1,
        "p_star_hat": p_star,
        "lhs": lhs,
        "rhs": rhs,
        "identity_gap": gap,
        "accuracy_increased": fic > fci,
    }


def _records_by_agent(records: list[dict]) -> dict:
    grouped = defaultdict(dict)
    for row in records:
        if not all(key in row for key in ("item", "agent", "round", "correct")):
            continue
        grouped[(str(row["item"]), str(row["agent"]))][int(row["round"])] = row
    return grouped


def dual_transition_tables(records: list[dict]) -> dict:
    """Return peer-count and same-answer transition cells for adjacent rounds."""
    grouped = _records_by_agent(records)
    by_item = defaultdict(dict)
    for (item, agent), states in grouped.items():
        by_item[item][agent] = states
    correct_cells = defaultdict(lambda: [0, 0])
    answer_cells = defaultdict(lambda: [0, 0, 0])
    for agents in by_item.values():
        rounds = sorted({r for state in agents.values() for r in state})
        for current, following in zip(rounds, rounds[1:]):
            present = [
                state
                for state in agents.values()
                if current in state and following in state
            ]
            for state in present:
                own = int(bool(state[current]["correct"]))
                peers_correct = (
                    sum(int(bool(other[current]["correct"])) for other in present) - own
                )
                key = (own, peers_correct)
                cell = correct_cells[key]
                cell[0] += int(bool(state[following]["correct"]))
                cell[1] += 1
                if (
                    "answer" in state[current]
                    and state[current].get("answer") is not None
                ):
                    agreeing = (
                        sum(
                            other[current].get("answer") == state[current].get("answer")
                            for other in present
                        )
                        - 1
                    )
                    share = round(agreeing / max(1, len(present) - 1), 2)
                    answer_cell = answer_cells[(own, share)]
                    answer_cell[0] += int(
                        state[following].get("answer") == state[current].get("answer")
                    )
                    answer_cell[1] += int(bool(state[following]["correct"]))
                    answer_cell[2] += 1
    by_correct = {}
    for key, (next_correct, n) in sorted(correct_cells.items()):
        p = next_correct / n
        by_correct[key] = {
            "p_correct_next": p,
            "p_switch": p if key[0] == 0 else 1.0 - p,
            "n": n,
        }
    by_answer = {}
    for key, (stay, next_correct, n) in sorted(answer_cells.items()):
        by_answer[key] = {
            "p_stay_own_answer": stay / n,
            "p_correct_next": next_correct / n,
            "n": n,
        }
    return {"by_correct_peers": by_correct, "by_same_answer_peers": by_answer}


def _cell_parts(key: Any) -> tuple[int, int]:
    if isinstance(key, tuple):
        return int(key[0]), int(key[1])
    parts = str(key).replace("=", " ").replace(",", " ").split()
    return int(parts[1]), int(parts[3])


def fit_influence_models(by_correct_peers: dict, k_agents: int) -> dict:
    if k_agents < 2:
        raise ValueError("k_agents must be at least 2")
    observations = []
    for key, cell in by_correct_peers.items():
        own, peers_correct = _cell_parts(key)
        opposing = peers_correct if own == 0 else (k_agents - 1 - peers_correct)
        x = max(0.0, min(1.0, opposing / (k_agents - 1)))
        y = float(cell.get("p_switch", cell.get("p_correct_next", 0.0)))
        if "p_switch" not in cell and own == 1:
            y = 1.0 - y
        observations.append((own, x, y, float(cell.get("n", 1))))
    if not observations:
        raise ValueError("no transition cells")
    models = {}
    for name, power in (
        ("constant", 0),
        ("linear_martingale", 1),
        ("convex_amplification", 2),
    ):
        params = {}
        residual = 0.0
        n_obs = 0
        for own in (0, 1):
            cells = [(x, y, n) for state, x, y, n in observations if state == own]
            if not cells:
                params["a" if own == 0 else "b"] = 0.0
                continue
            design = np.array([1.0 if power == 0 else x**power for x, _, _ in cells])
            values = np.array([y for _, y, _ in cells])
            weights = np.array([n for _, _, n in cells])
            denom = float(np.sum(weights * design * design))
            estimate = (
                float(np.sum(weights * design * values) / denom) if denom else 0.0
            )
            estimate = max(0.0, min(1.0, estimate))
            params["a" if own == 0 else "b"] = estimate
            residual += float(np.sum(weights * (values - estimate * design) ** 2))
            n_obs += len(cells)
        a, b = params.get("a", 0.0), params.get("b", 0.0)
        aic = n_obs * math.log(max(residual / max(1, n_obs), 1e-12)) + 4
        models[name] = {"a": a, "b": b, "wRSS": residual, "AIC": aic, "n_cells": n_obs}
    best = min(models, key=lambda name: models[name]["AIC"])
    return {"models": models, "best_model": best}


def _replicate_id(row: dict) -> tuple[str, str]:
    item = str(row["item"])
    if "#" in item:
        base, suffix = item.rsplit("#", 1)
        return base, str(row.get("replicate", suffix))
    if row.get("replicate") is not None:
        return item, str(row["replicate"])
    return item, "0"


def replicate_correlation_decomposition(
    records: list[dict], round_num: int = 1
) -> dict:
    grouped = defaultdict(lambda: defaultdict(dict))
    for row in records:
        if int(row.get("round", -1)) != round_num:
            continue
        base, replicate = _replicate_id(row)
        grouped[base][replicate][str(row["agent"])] = int(bool(row["correct"]))
    values = [
        value
        for reps in grouped.values()
        for agents in reps.values()
        for value in agents.values()
    ]
    p_bar = float(np.mean(values)) if values else None
    same = []
    different = []
    for reps in grouped.values():
        for agents in reps.values():
            vals = list(agents.values())
            same.extend(a * b for i, a in enumerate(vals) for b in vals[i + 1 :])
        rep_values = list(reps.values())
        for i, left in enumerate(rep_values):
            for right in rep_values[i + 1 :]:
                different.extend(a * b for a in left.values() for b in right.values())
    c_same = float(np.mean(same)) if same else None
    c_diff = float(np.mean(different)) if different else None
    denominator = p_bar * (1 - p_bar) if p_bar is not None else 0.0
    rho_total = (
        (c_same - p_bar**2) / denominator
        if denominator and c_same is not None
        else None
    )
    rho_item = (
        (c_diff - p_bar**2) / denominator
        if denominator and c_diff is not None
        else None
    )
    rho_within = (
        ((c_same - c_diff) / (p_bar - c_diff))
        if c_same is not None and c_diff is not None and p_bar != c_diff
        else None
    )
    k = max(
        (len(agents) for reps in grouped.values() for agents in reps.values()),
        default=0,
    )
    clipped = min(1.0, max(0.0, rho_within)) if rho_within is not None else None
    k_eff = k / (1 + (k - 1) * clipped) if clipped is not None and k else None
    return {
        "p_bar": p_bar,
        "c_same": c_same,
        "c_diff": c_diff,
        "rho_total": rho_total,
        "rho_item": rho_item,
        "rho_within": rho_within,
        "k_eff_within": k_eff,
        "round1_independence_pass": abs(rho_within) < 0.05
        if round_num == 1 and rho_within is not None
        else None,
        "n_items": len(grouped),
        "n_replicated_items": sum(len(reps) >= 2 for reps in grouped.values()),
    }
