"""Standalone PACE resource vectors and card exports."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_log(path: str) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError("empty PACE log")
    required = {"item", "agent", "round", "correct"}
    if not all(required <= set(row) for row in rows):
        raise ValueError("PACE logs require item, agent, round, and correct")
    return rows


def resource_vector(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    items = {str(row["item"]) for row in rows}
    n_items = max(1, len(items))
    calls = len(rows)
    rounds = {int(row["round"]) for row in rows}
    # Independent trajectories per item = calls made in the item's first round, before any communication (an agent that answers again in a later round is the same trajectory, not a new sample)
    first_round, later_calls = {}, 0
    for row in rows:
        first_round.setdefault(str(row["item"]), int(row["round"]))
        first_round[str(row["item"])] = min(first_round[str(row["item"])], int(row["round"]))
    trajectories = {}
    for row in rows:
        key = str(row["item"])
        if int(row["round"]) == first_round[key]:
            trajectories[key] = trajectories.get(key, 0) + 1
        else:
            later_calls += 1
    token_values = [
        float(row["prompt_tokens"]) + float(row["completion_tokens"])
        for row in rows
        if row.get("prompt_tokens") is not None
        and row.get("completion_tokens") is not None
    ]
    reason_values = [
        float(row["reasoning_tokens"])
        for row in rows
        if row.get("reasoning_tokens") is not None
    ]
    cost_values = [
        float(row["cost_usd"])
        for row in rows
        if row.get("cost_usd") is not None
    ]
    lat_values = [
        float(row["latency_s"])
        for row in rows
        if row.get("latency_s") is not None
    ]
    return {
        "r_reason": (sum(reason_values) / n_items) if reason_values else None,
        "r_token": (sum(token_values) / n_items) if token_values else None,
        "r_cost": (sum(cost_values) / n_items) if cost_values else None,
        "r_lat": (sum(lat_values) / n_items) if lat_values else None,
        "r_sample": sum(trajectories.values()) / n_items,
        "r_sys": float(
            sum(1 for row in rows if row.get("tool_calls")) / n_items
        ),
        "r_call": calls / n_items,
        "r_round": float(max(rounds) - min(rounds) + 1),
        "r_context": later_calls / n_items,
        "r_scaff": float(
            sum(1 for row in rows if row.get("scaffold") or row.get("tool_calls"))
        ),
    }


def classify_baseline(vector: dict[str, float | None]) -> str:
    """Rung (A, B or C) that this log would occupy as a single-agent baseline, following Table 7 of the paper; "n/a" if the log is a multi-agent system.

    A: one greedy-style pass (one trajectory, one round, no later-round context). B: several independent trajectories in one round (sampled; no named
    resource is known to be matched). C: one trajectory refined over several rounds (a named resource, the iteration count, may be matched; confirm with
    `pace classify`). Rung D (the Pareto frontier) is a property of a family of runs and cannot be read from one log.
    """
    return classify_baseline_detail(vector)[0]


def classify_baseline_detail(vector: dict[str, float | None]) -> tuple[str, str]:
    r_round = float(vector.get("r_round") or 0.0)
    r_sample = float(vector.get("r_sample") or 0.0)
    r_context = float(vector.get("r_context") or 0.0)
    if r_round <= 1 and r_sample <= 1 and r_context <= 0:
        return "A", "one trajectory, one round"
    if r_round <= 1 and r_context <= 0:
        return "B", "%.3g independent trajectories in one round, no resource known to be matched" % r_sample
    if r_sample <= 1:
        return "C", "one trajectory over %.3g rounds; C only if the iteration ceiling is matched" % r_round
    return "n/a", "several trajectories with later-round communication: a multi-agent system, not a single-agent baseline"


def feasibility(vector: dict[str, float | None]) -> dict[str, Any]:
    if vector.get("r_token") is None:
        return {
            "status": "insufficient_data",
            "active_axes": [k for k, v in vector.items() if v is not None and v > 0],
            "direction": "missing token logs",
        }
    positive = [key for key, value in vector.items() if value is not None and value > 0]
    return {
        "status": "measured_only" if positive else "insufficient_data",
        "active_axes": positive,
        "direction": "requires baseline comparison for directional feasibility",
    }


def transition_matrix(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    grouped = defaultdict(dict)
    for row in rows:
        grouped[(str(row["item"]), str(row["agent"]))][int(row["round"])] = bool(
            row["correct"]
        )
    counts = defaultdict(lambda: [0, 0])
    by_item = defaultdict(dict)
    for (item, agent), states in grouped.items():
        by_item[item][agent] = states
    for agents in by_item.values():
        rounds = sorted({round_no for states in agents.values() for round_no in states})
        for current, following in zip(rounds, rounds[1:]):
            present = [
                states
                for states in agents.values()
                if current in states and following in states
            ]
            for states in present:
                peers_right = sum(int(other[current]) for other in present) - int(
                    states[current]
                )
                key = "own=%d,peers_right=%d" % (int(states[current]), peers_right)
                counts[key][0] += int(states[following])
                counts[key][1] += 1
    return {
        key: {"p_next": good / total, "n": total}
        for key, (good, total) in counts.items()
    }


def build_card(rows: list[dict[str, Any]]) -> dict[str, Any]:
    vector = resource_vector(rows)
    return {
        "schema": "pace-card/v1",
        "n_records": len(rows),
        "n_items": len({str(row["item"]) for row in rows}),
        "resource_vector": vector,
        "baseline": classify_baseline(vector),
        "baseline_reason": classify_baseline_detail(vector)[1],
        "feasibility": feasibility(vector),
        "transition_matrix": transition_matrix(rows),
    }


def to_markdown(card: dict[str, Any]) -> str:
    lines = [
        "# PACE Card",
        "",
        "| Field | Value |",
        "|---|---:|",
        "| Baseline | %s |" % card["baseline"],
        "| Items | %s |" % card["n_items"],
    ]
    lines += [
        "| %s | %s |" % (key, ("%.3f" % value if value is not None else "n/a"))
        for key, value in card["resource_vector"].items()
    ]
    lines += [
        "",
        "## Transition matrix",
        "",
        "| State | P(correct at t+1) | n |",
        "|---|---:|---:|",
    ]
    lines += [
        "| %s | %.3f | %d |" % (key, value["p_next"], value["n"])
        for key, value in card["transition_matrix"].items()
    ]
    return "\n".join(lines) + "\n"


def to_latex(card: dict[str, Any]) -> str:
    rows = [
        "\\begin{tcolorbox}[title={PACE Card}]",
        "\\textbf{Baseline:} %s\\par" % card["baseline"],
        "\\begin{tabular}{lr}",
        "\\toprule",
        "Axis & Value\\\\",
        "\\midrule",
    ]
    rows += [
        "%s & %s\\\\" % (key.replace("_", "\\_"), ("%.3f" % value if value is not None else "n/a"))
        for key, value in card["resource_vector"].items()
    ]
    rows += ["\\bottomrule", "\\end{tabular}", "\\end{tcolorbox}"]
    return "\n".join(rows) + "\n"
