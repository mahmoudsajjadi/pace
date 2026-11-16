"""Dependency-light PACE Phase 16 protocol and constructive objective engine."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean, median, pstdev

import numpy as np


def _get(row, *names, default=0.0):
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return default


def _float(row, *names, default=0.0):
    try:
        return float(_get(row, *names, default=default))
    except (TypeError, ValueError):
        return float(default)


def _item(row):
    return str(_get(row, "item", "id", "item_id", default="item"))


def _accuracy(row):
    value = _get(row, "correct", "accuracy", "score", default=0.0)
    return (
        float(value)
        if isinstance(value, (int, float))
        else float(str(value).lower() in {"1", "true", "correct", "yes"})
    )


def _bootstrap(values, statistic, n_boot, seed):
    values = np.asarray(list(values), dtype=float)
    if not len(values):
        return [None, None]
    rng = np.random.default_rng(seed)
    draws = [
        statistic(values[rng.integers(0, len(values), len(values))])
        for _ in range(max(1, n_boot))
    ]
    return [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))]


def itemwise_resource_match(mas_rows, pool_rows, axis="tokens", n_boot=500, seed=0):
    if axis not in {"tokens", "calls", "cost"}:
        raise ValueError("axis must be tokens, calls, or cost")
    pools = defaultdict(list)
    for row in pool_rows:
        pools[_item(row)].append(
            max(0.0, _float(row, axis, f"{axis}_total", "resource"))
        )
    mas = defaultdict(list)
    for row in mas_rows:
        mas[_item(row)].append(row)
    ks, frontier, observed, statuses = [], [], [], []
    for item, rows in mas.items():
        budget = sum(
            max(0.0, _float(r, axis, f"{axis}_total", "resource")) for r in rows
        )
        samples = pools.get(item, []) or [0.0]
        cumulative = 0.0
        k = 0
        for value in samples:
            k += 1
            cumulative += value
            if cumulative >= budget:
                break
        statuses.append("reached" if cumulative >= budget else "exhausted")
        ks.append(max(1, k))
        frontier.append(
            float(
                np.mean(
                    [_accuracy(r) for r in pool_rows if _item(r) == item][:k] or [0.0]
                )
            )
        )
        observed.append(float(np.mean([_accuracy(r) for r in rows])))
    gap = [a - b for a, b in zip(observed, frontier)]
    result = {
        "n_items": len(ks),
        "mean_k_i": float(mean(ks)) if ks else 0.0,
        "median_k_i": float(median(ks)) if ks else 0.0,
        "max_k_i": max(ks) if ks else 0,
        "mas_accuracy": float(mean(observed)) if observed else 0.0,
        "itemwise_frontier_accuracy": float(mean(frontier)) if frontier else 0.0,
        "expectation_frontier_accuracy": float(mean(frontier)) if frontier else 0.0,
        "itemwise_gap": float(mean(gap)) if gap else 0.0,
        "expectation_gap": float(mean(observed) - mean(frontier)) if gap else 0.0,
        "ci_low": None,
        "ci_high": None,
        "paired_bootstrap_ci": _bootstrap(gap, np.mean, n_boot, seed),
        "itemwise_dominance_share": float(sum(x >= 0 for x in gap) / len(gap))
        if gap
        else 0.0,
        "range_status": dict(Counter(statuses)),
        "axis": axis,
    }
    result["ci_low"], result["ci_high"] = result["paired_bootstrap_ci"]
    return result


def _distribution(values):
    values = [float(x) for x in values]
    if not values:
        return {
            key: 0.0
            for key in ("mean", "std", "min", "p25", "median", "p75", "p90", "max")
        }
    return {
        "mean": float(mean(values)),
        "std": float(pstdev(values)),
        "min": min(values),
        "p25": float(np.percentile(values, 25)),
        "median": float(median(values)),
        "p75": float(np.percentile(values, 75)),
        "p90": float(np.percentile(values, 90)),
        "max": max(values),
    }


def adaptive_stopping_audit(rows, declared_ceiling=None):
    by_item = defaultdict(list)
    for row in rows:
        by_item[_item(row)].append(row)
    rounds = [
        max(_float(r, "rounds", "round", default=1) for r in rs)
        for rs in by_item.values()
    ]
    calls = [sum(_float(r, "calls", default=1) for r in rs) for rs in by_item.values()]
    tokens = [
        sum(
            _float(r, "tokens", "prompt_tokens", default=0)
            + _float(r, "completion_tokens", default=0)
            for r in rs
        )
        for rs in by_item.values()
    ]
    ceiling = (
        declared_ceiling
        if declared_ceiling is not None
        else (max(rounds) if rounds else 0)
    )
    reasons = Counter(
        str(_get(r, "termination_reason", "done_reason", default="unspecified"))
        for r in rows
    )
    return {
        "n_items": len(by_item),
        "rounds": _distribution(rounds),
        "calls": _distribution(calls),
        "tokens": _distribution(tokens),
        "declared_ceiling": ceiling,
        "ceiling_compliance_rate": float(
            sum(x <= ceiling for x in rounds) / len(rounds)
        )
        if rounds
        else 1.0,
        "early_stop_share": float(sum(x < ceiling for x in rounds) / len(rounds))
        if rounds
        else 0.0,
        "termination_reasons": dict(reasons),
    }


def cache_adjusted_accounting(rows, alphas=(0.0, 0.1, 0.25, 0.5, 1.0), alpha_out=1.0):
    by_item = defaultdict(lambda: {"uncached": 0.0, "cached": 0.0, "out": 0.0})
    for row in rows:
        item = _item(row)
        by_item[item]["uncached"] += _float(
            row, "input_uncached", "prompt_tokens", default=0
        )
        by_item[item]["cached"] += _float(
            row, "input_cached", "cached_prompt_tokens", default=0
        )
        by_item[item]["out"] += _float(
            row, "output_tokens", "completion_tokens", default=0
        )
    raw = [v["uncached"] + v["cached"] + v["out"] for v in by_item.values()]
    adjusted = {
        str(alpha): [
            v["uncached"] + alpha * v["cached"] + alpha_out * v["out"]
            for v in by_item.values()
        ]
        for alpha in alphas
    }
    return {
        "n_items": len(by_item),
        "raw_totals": {"total": sum(raw), "mean": float(mean(raw)) if raw else 0.0},
        "adjusted_totals": {
            a: {"total": sum(values), "mean": float(mean(values)) if values else 0.0}
            for a, values in adjusted.items()
        },
        "alphas": list(alphas),
        "alpha_out": alpha_out,
    }


def classify_hybrid_call_graph(rows):
    by_item = defaultdict(list)
    for row in rows:
        by_item[_item(row)].append(row)
    records = []
    for item, values in by_item.items():
        independent = len(
            {
                str(_get(r, "thread", "agent", "model", default="default"))
                for r in values
            }
        )
        self_edges = cross_edges = aggregation = judge = tools = 0
        for row in values:
            kind = str(_get(row, "call_type", "role", "type", default="")).lower()
            source = _get(
                row, "reads_from", "parent_thread", "source_thread", default=None
            )
            if source not in (None, "", "none"):
                cross_edges += (
                    1
                    if str(source) != str(_get(row, "thread", "agent", default=""))
                    else 0
                )
                self_edges += (
                    1
                    if str(source) == str(_get(row, "thread", "agent", default=""))
                    else 0
                )
            aggregation += int(any(x in kind for x in ("aggregate", "vote", "synth")))
            judge += int("judge" in kind or "verif" in kind)
            tools += int("tool" in kind)
        records.append(
            {
                "item": item,
                "independent_trajectories": independent,
                "self_continuation_edges": self_edges,
                "cross_thread_edges": cross_edges,
                "aggregation_calls": aggregation,
                "judge_calls": judge,
                "tool_calls": tools,
            }
        )
    policy = (
        "Pi_agent" if any(r["cross_thread_edges"] for r in records) else "Pi_single"
    )
    keys = (
        "independent_trajectories",
        "self_continuation_edges",
        "cross_thread_edges",
        "aggregation_calls",
        "judge_calls",
        "tool_calls",
    )
    return {
        "policy_class": policy,
        "n_items": len(records),
        "per_item": records,
        "mean_counts": {
            key: float(mean([r[key] for r in records])) if records else 0.0
            for key in keys
        },
        "total_counts": {key: sum(r[key] for r in records) for key in keys},
    }


def evaluate_constructive_objectives(
    comm_rows,
    placebo_rows,
    full_base_rows,
    ver_rows=None,
    cost_mas=None,
    cost_base=None,
):
    def paired(a, b):
        n = min(len(a), len(b))
        differences = [float(a[i]) - float(b[i]) for i in range(n)]
        return (
            float(mean(a[:n])),
            float(mean(b[:n])),
            _bootstrap(differences, np.mean, 500, 0),
        )

    p_comm, p_placebo, ci_arch = paired(comm_rows, placebo_rows)
    _, p_full, ci_over = paired(full_base_rows, placebo_rows)
    p1 = p_placebo
    tau_ic = sum(1 for a, b in zip(placebo_rows, comm_rows) if not a and b) / max(
        1, sum(1 for a in placebo_rows if not a)
    )
    tau_ci = sum(1 for a, b in zip(placebo_rows, comm_rows) if a and not b) / max(
        1, sum(1 for a in placebo_rows if a)
    )
    threshold = p1 / (1 - p1) if p1 < 1 else float("inf")
    delta_c = (
        None if cost_mas is None or cost_base is None else float(cost_mas - cost_base)
    )
    return {
        "placebo_overhead": {
            "p_comm": p_comm,
            "p_placebo": p_placebo,
            "p_full": p_full,
            "delta_arch": p_comm - p_placebo,
            "delta_overhead": p_full - p_placebo,
            "net_comm_minus_full": p_comm - p_full,
            "ci_arch": ci_arch,
            "ci_overhead": ci_over,
            "arch_exceeds_overhead": p_comm - p_placebo > p_full - p_placebo,
        },
        "verifier_conformity": {
            "p1": p1,
            "tau_i_to_c": tau_ic,
            "tau_c_to_i": tau_ci,
            "delta_p_agg": p_comm - p_placebo,
            "delta_p_ver": None if ver_rows is None else mean(ver_rows) - p1,
            "threshold": threshold,
            "kappa": tau_ic / tau_ci if tau_ci else float("inf"),
            "exceeds_conformity_threshold": tau_ic > threshold * tau_ci,
        },
        "cost": {
            "delta_C": delta_c,
            "cost_saving_achieved": None if delta_c is None else delta_c < 0,
            "joint_efficiency_win": None
            if delta_c is None
            else delta_c < 0 and p_comm >= p_full,
        },
    }


def build_evaluation_card_v7(rows, baseline_rows=None, alphas=(0.1, 0.5)):
    resource = {
        "tokens": sum(
            _float(r, "tokens", "prompt_tokens", "completion_tokens") for r in rows
        ),
        "calls": len(rows),
        "cost": sum(_float(r, "cost", "cost_usd") for r in rows),
    }
    base = sum(
        _float(r, "tokens", "prompt_tokens", "completion_tokens")
        for r in (baseline_rows or [])
    )
    ratio = resource["tokens"] / base if base else "unreported"
    card = {
        "baseline_rung": "unreported",
        "resource_vector": resource,
        "token_accounting": cache_adjusted_accounting(rows, alphas),
        "resource_ratios": {
            "tokens_mas_over_baseline": ratio,
            "calls_mas_over_baseline": len(rows) / len(baseline_rows)
            if baseline_rows
            else "unreported",
            "cost_mas_over_baseline": "unreported",
        },
        "frontier_gap": {
            "accuracy": mean([_accuracy(r) for r in rows]) if rows else 0.0,
            "baseline_accuracy": mean([_accuracy(r) for r in baseline_rows])
            if baseline_rows
            else "unreported",
            "gap": "unreported",
        },
        "evidence_and_routes": {
            "n_rows": len(rows),
            "routes": sorted(
                {str(_get(r, "strategy", "route", default="unreported")) for r in rows}
            ),
        },
        "resource_distribution_and_stopping": adaptive_stopping_audit(rows),
        "reporting_level_achieved": "PACE-Recommended",
    }
    return card


def card_v7_to_latex(card):
    def clean(value):
        text = (
            str(value).replace("n/a", "unreported").replace("in progress", "unreported")
        )
        return text.replace("&", r"\&")

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\small",
        r"\caption{PACE evaluation card v7.}",
        r"\label{tab:pace_card_v7}",
        r"\begin{tabular}{ll}",
        r"\toprule",
        "Field & Value \\",
        r"\midrule",
    ]
    for key in (
        "baseline_rung",
        "resource_vector",
        "token_accounting",
        "resource_ratios",
        "frontier_gap",
        "evidence_and_routes",
        "resource_distribution_and_stopping",
        "reporting_level_achieved",
    ):
        lines.append(f"{clean(key)} & {clean(card.get(key))} \\")
    return "\n".join(lines + [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])


def card_v7_to_markdown(card):
    return (
        "\n".join(
            ["| Field | Value |", "|---|---|"]
            + [f"| {key} | {value} |" for key, value in card.items()]
        )
        + "\n"
    )
