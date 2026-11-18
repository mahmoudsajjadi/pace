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
        "r_lat": (sum(lat_values) / n_items) if lat_values else None,   # summed call latency per item (serialised sum, not the critical path)
        "r_sample": sum(trajectories.values()) / n_items,
        # external tool or verifier calls per item; None (shown as n/a) when no row carries a tool_calls field at all (absent is not the same as zero)
        "r_sys": (
            float(sum(1 for row in rows if row.get("tool_calls")) / n_items)
            if any("tool_calls" in row for row in rows)
            else None
        ),
        "r_call": calls / n_items,
        "r_round": float(max(rounds) - min(rounds) + 1),
        "r_context": later_calls / n_items,
        "r_scaff": float(
            sum(1 for row in rows if row.get("scaffold") or row.get("tool_calls"))
        )
        / n_items,   # scaffold or tool calls per item (was a total over the log before card schema v2)
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
        "direction": "requires compute-matched baseline comparison",
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
    def order(key: str) -> tuple[int, int]:
        own, peers = key.split(",")
        return int(own.split("=")[1]), int(peers.split("=")[1])

    return {
        key: {"p_next": counts[key][0] / counts[key][1], "n": counts[key][1]}
        for key in sorted(counts, key=order)
    }


RULED_OUT = "RULED OUT BY NESTED ROUND-1 VOTE"


def _is_right(value: Any) -> bool:
    return value in (True, 1, 1.0, "1", "true", "True")


def _vote_credit(round_rows: list[dict[str, Any]]) -> float:
    """Credit of a vote over the answers of one item in one round. With an `answer` label on every row: plurality, a tie of m leaders credits the share of
    correct leaders. Without labels: binary majority of the `correct` flags (a tie credits 0.5)."""
    if round_rows and all("answer" in row for row in round_rows):
        groups: dict[str, list[bool]] = defaultdict(list)
        for row in round_rows:
            groups[str(row["answer"])].append(_is_right(row["correct"]))
        top = max(len(v) for v in groups.values())
        leaders = [v for v in groups.values() if len(v) == top]
        return sum(1.0 for v in leaders if any(v)) / len(leaders)
    right = sum(1 for row in round_rows if _is_right(row["correct"]))
    wrong = len(round_rows) - right
    return 1.0 if right > wrong else (0.5 if right == wrong else 0.0)


def single_trace_decomposition(rows: list[dict[str, Any]], n_boot: int = 200, seed: int = 20261117) -> dict[str, Any] | None:
    """Zero-extra-call counterfactual decomposition of one multi-round, multi-agent trace (needs r_round > 1 and r_sample >= 2).

    The round-1 answers of the agents are independent samples, so a vote over them is a nested Category B baseline that costs nothing beyond the trace.
      p_round1_single  mean correctness of a round-1 answer          p_round1_vote  accuracy of the vote over the round-1 answers
      p_final_vote     accuracy of the vote over the last-round answers
      delta_nested_B   p_final_vote - p_round1_vote, paired bootstrap 95% interval over items ({n_boot} resamples); <= 0 is flagged RULED OUT BY NESTED ROUND-1 VOTE
      k_tok_empirical  total tokens per item divided by the mean tokens of a round-1 call (samples that the trace's token spend would buy)
      p_projected_cat_C  accuracy of a vote over round(k_tok_empirical) samples under the beta-binomial fit of the round-1 successes (`pace inflate`; plurality
                       over W wrong options when rows carry `answer`, binary majority otherwise)
    """
    import random

    from .inflate import fit_beta_binomial, estimate_wrong_options, plurality_accuracy, successes_from_rows, vote_accuracy

    vector = resource_vector(rows)
    if float(vector.get("r_round") or 0) <= 1 or float(vector.get("r_sample") or 0) < 2:
        return None
    by_item: dict[str, dict[int, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        by_item[str(row["item"])][int(row["round"])].append(row)
    first = min(int(row["round"]) for row in rows)
    last = max(int(row["round"]) for row in rows)
    items = sorted(i for i, r in by_item.items() if first in r and last in r)
    if not items:
        return None
    r1_single = [sum(_is_right(r["correct"]) for r in by_item[i][first]) / len(by_item[i][first]) for i in items]
    r1_vote = [_vote_credit(by_item[i][first]) for i in items]
    fin_vote = [_vote_credit(by_item[i][last]) for i in items]
    diff = [f - v for f, v in zip(fin_vote, r1_vote)]
    delta = sum(diff) / len(diff)
    rng = random.Random(seed)
    boots = sorted(sum(diff[rng.randrange(len(diff))] for _ in diff) / len(diff) for _ in range(n_boot))
    lo, hi = boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot) - 1]
    tok_all = [float(r["prompt_tokens"]) + float(r["completion_tokens"]) for r in rows if r.get("prompt_tokens") is not None and r.get("completion_tokens") is not None]
    tok_r1 = [float(r["prompt_tokens"]) + float(r["completion_tokens"]) for i in items for r in by_item[i][first] if r.get("prompt_tokens") is not None and r.get("completion_tokens") is not None]
    k_tok = None
    projected = None
    if tok_all and tok_r1 and len(tok_all) == len(rows):
        k_tok = (sum(tok_all) / len(by_item)) / (sum(tok_r1) / len(tok_r1))
        r1_rows = [r for i in items for r in by_item[i][first]]
        succ, n = successes_from_rows(r1_rows)
        if succ and n >= 2:
            a, b = fit_beta_binomial(succ, n)
            K = max(1, int(round(k_tok)))
            W = estimate_wrong_options(r1_rows) if all("answer" in r for r in r1_rows) else None
            # the plurality closed form is exact but slow for large K or W: cap W at 20 (lowers the projection, so it stays conservative) and fall back to the binary majority above K = 40
            projected = plurality_accuracy(a, b, K, min(W, 20.0)) if (W is not None and K <= 40) else vote_accuracy(a, b, K)
    return {
        "n_items": len(items),
        "p_round1_single": sum(r1_single) / len(items),
        "p_round1_vote": sum(r1_vote) / len(items),
        "p_final_vote": sum(fin_vote) / len(items),
        "delta_nested_B": delta,
        "delta_nested_B_ci95": [lo, hi],
        "n_boot": n_boot,
        "flag": RULED_OUT if delta <= 0 else None,
        "k_tok_empirical": k_tok,
        "p_projected_cat_C": projected,
    }


def build_card(rows: list[dict[str, Any]]) -> dict[str, Any]:
    vector = resource_vector(rows)
    trace = single_trace_decomposition(rows)
    card = {
        "schema": "pace-card/v1",
        "n_records": len(rows),
        "n_items": len({str(row["item"]) for row in rows}),
        "resource_vector": vector,
        "baseline": classify_baseline(vector),
        "baseline_reason": classify_baseline_detail(vector)[1],
        "feasibility": feasibility(vector),
        "transition_matrix": transition_matrix(rows),
    }
    if trace is not None:
        card["single_trace"] = trace
    return card


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
    st = card.get("single_trace")
    if st:
        f = lambda v: "n/a" if v is None else "%.3f" % v  # noqa: E731
        lines += ["", "## Single-trace counterfactual (zero extra calls)", "", "| Quantity | Value |", "|---|---:|",
                  "| p_round1_single | %s |" % f(st["p_round1_single"]), "| p_round1_vote | %s |" % f(st["p_round1_vote"]), "| p_final_vote | %s |" % f(st["p_final_vote"]),
                  "| delta_nested_B [95%% CI] | %s [%s, %s] |" % (f(st["delta_nested_B"]), f(st["delta_nested_B_ci95"][0]), f(st["delta_nested_B_ci95"][1])),
                  "| k_tok_empirical | %s |" % f(st["k_tok_empirical"]), "| p_projected_cat_C | %s |" % f(st["p_projected_cat_C"])]
        if st.get("flag"):
            lines += ["", "**%s**" % st["flag"]]
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


# ---------------------------------------------------------------------------------------------------------------------------------------------
# PACE Evaluation Card, schema v2: five sections (A identity, B resource accounting, C baseline specification, D statistical evidence, E reproducibility)
# ---------------------------------------------------------------------------------------------------------------------------------------------
CARD_V2_VERSION = "pace-card/v2"
CITATION_INSTRUCTIONS = (
    "Cite the framework paper (PACE: Parity-Aware Compute Evaluation), the pace-eval package version recorded in section E, and the dataset DOI of the contrast corpus; "
    "report this card with the execution log it was computed from."
)

CARD_V2_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "PACE Evaluation Card",
    "type": "object",
    "required": ["schema", "A_identity", "B_resource_accounting", "C_baseline_specification", "D_statistical_evidence", "E_reproducibility"],
    "properties": {
        "schema": {"const": CARD_V2_VERSION},
        "A_identity": {"type": "object", "required": ["name", "system", "task", "model", "n_items"],
                       "properties": {"name": {"type": ["string", "null"]}, "system": {"type": ["string", "null"]}, "task": {"type": ["string", "null"]},
                                      "model": {"type": ["string", "null"]}, "n_items": {"type": "integer", "minimum": 0}, "n_records": {"type": "integer", "minimum": 0}}},
        "B_resource_accounting": {"type": "object", "required": ["axes", "latency"],
                                  "properties": {"axes": {"type": "object", "additionalProperties": {"type": ["number", "null"]}},
                                                 "latency": {"type": "object", "required": ["summed_s_per_item", "critical_path_s_per_item"],
                                                             "properties": {"summed_s_per_item": {"type": ["number", "null"]}, "critical_path_s_per_item": {"type": ["number", "null"]}}},
                                                 "unmeasured": {"type": "array", "items": {"type": "string"}}}},
        "C_baseline_specification": {"type": "object", "required": ["rung", "reason"],
                                     "properties": {"rung": {"enum": ["A", "B", "C", "n/a"]}, "reason": {"type": "string"}, "matched_axes": {"type": "array", "items": {"type": "string"}}}},
        "D_statistical_evidence": {"type": "object", "required": ["single_trace"],
                                   "properties": {"single_trace": {"type": ["object", "null"]}, "transition_matrix": {"type": "object"}}},
        "E_reproducibility": {"type": "object", "required": ["pace_version", "log_sha256", "citation_instructions"],
                              "properties": {"pace_version": {"type": "string"}, "log_sha256": {"type": ["string", "null"]}, "citation_instructions": {"type": "string"}}},
    },
}


def critical_path_latency(rows: list[dict[str, Any]]) -> float | None:
    """Mean over items of the critical path: calls inside one round are taken as concurrent, so each round contributes its slowest call and rounds add (None without latency_s)."""
    per_item: dict[str, dict[int, float]] = defaultdict(dict)
    seen = False
    for row in rows:
        if row.get("latency_s") is None:
            continue
        seen = True
        rd = int(row["round"])
        it = per_item[str(row["item"])]
        it[rd] = max(it.get(rd, 0.0), float(row["latency_s"]))
    if not seen:
        return None
    return sum(sum(r.values()) for r in per_item.values()) / len(per_item)


def build_card_v2(rows: list[dict[str, Any]], identity: dict[str, Any] | None = None, log_path: str | None = None) -> dict[str, Any]:
    """Five-section card. Unmeasured axes are null (and listed), never 0; latency is reported both summed and along the critical path."""
    import hashlib

    base = build_card(rows)
    vec = base["resource_vector"]
    ident = identity or {}
    axes = {k: vec[k] for k in ("r_reason", "r_token", "r_cost", "r_sample", "r_sys", "r_call", "r_round", "r_context", "r_scaff")}
    try:
        from . import __version__ as pace_version
    except ImportError:
        pace_version = "unknown"
    sha = hashlib.sha256(Path(log_path).read_bytes()).hexdigest() if log_path and Path(log_path).exists() else None
    return {
        "schema": CARD_V2_VERSION,
        "A_identity": {"name": ident.get("name"), "system": ident.get("system"), "task": ident.get("task"), "model": ident.get("model"),
                       "n_items": base["n_items"], "n_records": base["n_records"]},
        "B_resource_accounting": {"axes": axes, "latency": {"summed_s_per_item": vec["r_lat"], "critical_path_s_per_item": critical_path_latency(rows)},
                                  "unmeasured": sorted([k for k, v in axes.items() if v is None] + (["r_lat"] if vec["r_lat"] is None else []))},
        "C_baseline_specification": {"rung": base["baseline"], "reason": base["baseline_reason"], "matched_axes": base["feasibility"].get("active_axes", [])},
        "D_statistical_evidence": {"single_trace": base.get("single_trace"), "transition_matrix": base["transition_matrix"]},
        "E_reproducibility": {"pace_version": pace_version, "log_sha256": sha, "citation_instructions": CITATION_INSTRUCTIONS},
    }


def to_latex_v2(card: dict[str, Any]) -> str:
    """Compact LaTeX snippet of a v2 card (five rows, one per section)."""
    B = chr(92)
    f = lambda v: "n/a" if v is None else ("%.3g" % v)  # noqa: E731
    b, c, d = card["B_resource_accounting"], card["C_baseline_specification"], card["D_statistical_evidence"]
    st = d.get("single_trace") or {}
    rows = [
        ("A. Identity", "%s items, %s records" % (card["A_identity"]["n_items"], card["A_identity"]["n_records"])),
        ("B. Resources", "tokens %s, calls %s, rounds %s; latency %s s summed, %s s critical path per item" % (f(b["axes"]["r_token"]), f(b["axes"]["r_call"]), f(b["axes"]["r_round"]),
                                                                                                          f(b["latency"]["summed_s_per_item"]), f(b["latency"]["critical_path_s_per_item"]))),
        ("C. Baseline", "rung %s (%s)" % (c["rung"], c["reason"])),
        ("D. Evidence", ("nested round-1 vote gap %s" % f(st.get("delta_nested_B"))) if st else "no multi-round trace"),
        ("E. Reproducibility", "pace %s, log SHA-256 %s" % (card["E_reproducibility"]["pace_version"], (card["E_reproducibility"]["log_sha256"] or "n/a")[:12])),
    ]
    out = [B + "begin{tabular}{@{}lp{0.75" + B + "linewidth}@{}}", B + "toprule"]
    out += ["%s & %s " % (k, v.replace("_", B + "_").replace("%", B + "%")) + B + B for k, v in rows]
    out += [B + "bottomrule", B + "end{tabular}"]
    return NL_JOIN.join(out) + NL_JOIN


NL_JOIN = "\n"


# ---------------------------------------------------------------------------------------------------------------------------------------------
# PACE Card v1.0 LaTeX table: the same seven rows, wording and escaping as latexV1() in PACE Studio and the Workbench (tests/test_cli_card_latex_and_validate.py compares them)
# ---------------------------------------------------------------------------------------------------------------------------------------------
def _tex_escape(s: str) -> str:
    out = str(s).replace("\\", "\\textbackslash{}")
    for ch in "_%&#$":
        out = out.replace(ch, "\\" + ch)
    return out


def _fixed(v: Any, digits: int) -> str:
    """Number.prototype.toFixed: round half up on the exact binary value; n/a for None or NaN."""
    from decimal import ROUND_HALF_UP, Decimal

    if v is None:
        return "n/a"
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "n/a"
    if x != x:
        return "n/a"
    q = Decimal(1).scaleb(-digits)
    return str(Decimal(x).quantize(q, rounding=ROUND_HALF_UP))


def to_latex_card_v1(card: dict[str, Any]) -> str:
    """The PACE Card v1.0 table (7 fields: reported value, level, command) for a card from build_card (or card_v2_base)."""
    R = card.get("resource_vector") or {}
    cells = len(card.get("transition_matrix") or {})
    f = _fixed
    rows = [
        ("1", "Baseline rung", "Category %s" % card["baseline"], "Min", "classify"),
        ("2", "Resource vector", "tokens %s, calls %s, rounds %s, samples %s, cost %s, latency %s s, tool calls %s" % (
            f(R.get("r_token"), 1), f(R.get("r_call"), 2), f(R.get("r_round"), 0), f(R.get("r_sample"), 2), f(R.get("r_cost"), 4), f(R.get("r_lat"), 2), f(R.get("r_sys"), 2)), "Min", "audit"),
        ("3", "Token accounting", "tokens per item %s; scaffold or tool rows %s" % (f(R.get("r_token"), 1), f(R.get("r_scaff"), 0)), "Min, Rec", "card -{}-v2"),
        ("4", "Resource ratios and feasibility", (card.get("feasibility") or {}).get("direction") or "n/a", "Rec", "audit"),
        ("5", "Frontier gap", "not computed in the browser; run pace report with a sample pool", "Min, Rec", "report"),
        ("6", "Evidence and routes", "%s items, %s calls, %s transition cells" % (card["n_items"], card["n_records"], cells), "Rec", "dynamics"),
        ("7", "Per-item budgets and search cost", "not computed in the browser; run pace card -{}-v2", "Ext", "card -{}-v2"),
    ]
    keep = "\x01"

    def esc(s: str) -> str:
        return _tex_escape(s.replace("-{}-", keep)).replace(keep, "-{}-")

    body = "\n".join("%s & %s & %s & \\texttt{%s} \\\\" % (r[0], esc("%s: %s" % (r[1], r[2])), r[3], esc(r[4])) for r in rows)
    return (
        "% PACE Card v1.0 (generated in the browser by PACE Studio; fields as in the paper, arXiv:2611.17610)\n\\begin{table}[t]\n\\centering\n\\footnotesize\n"
        "\\caption{PACE Card v1.0. Fields not computed from the log alone are marked; a dimension that was not measured is stated as n/a, never imputed.}\n"
        "\\begin{tabular}{@{}rp{0.62\\linewidth}ll@{}}\n\\toprule\n & Field: reported value & Level & Command \\\\\n\\midrule\n" + body + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )
