"""`pace compare`: pairwise resource parity and a directional feasibility verdict for two PACE traces (a reference baseline and a candidate under test).

Item credit: the mean ``correct`` over the rows of the item's last round, or the last non-null ``item_correct`` when the trace carries one (a flag, or a credit between 0 and 1 for a vote with ties; use it for a vote or a judge that the per-call flags do not show).
Only items present in both traces are compared. The accuracy gap is candidate minus baseline over those items, with a paired normal-approximation 95% interval (mean difference +- 1.96 SE of the
per-item differences). Resource ratios are candidate / baseline: ``r_token`` (tokens per item, prompt + completion), ``r_call`` (calls per item), ``r_latency_critical`` (critical-path seconds per item:
slowest call of each round, summed over rounds) and ``r_scaff`` (scaffold or tool rows per item); an axis that either trace did not measure is ``null``.

Verdict (the directional rule of the paper, on the token axis, with parity tolerance ``tol`` and smallest advantage of interest ``margin``):
  CREDITS       the interval of the gap is entirely above 0 and the candidate used at most (1 + tol) times the baseline's tokens, so the baseline had at least the candidate's budget and still lost;
  RULES OUT     the upper end of the interval is at most ``margin`` and the candidate used at least 1 / (1 + tol) times the baseline's tokens, so an advantage above the margin is excluded although the
                candidate was not short of resources;
  INCONCLUSIVE  anything else: fewer than ``min_items`` (default 20) shared items, tokens missing on a trace, a win bought with more than (1 + tol) times the tokens, a loss with fewer than 1 / (1 + tol) times the tokens, or an
                interval too wide to decide.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from .card import classify_baseline, critical_path_latency, resource_vector

SCHEMA = "pace-compare/v1"
LABELS = ("CREDITS", "RULES OUT", "INCONCLUSIVE")
AXES = ("r_token", "r_call", "r_latency_critical", "r_scaff")


def _num(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _flag(v: Any) -> bool:
    return v is True or v == 1 or str(v).strip().lower() in ("1", "true", "correct")


def _credit(v: Any) -> float:
    """A 0..1 credit: numbers (and numeric strings) are clamped to [0, 1], anything else is read as a correct/incorrect flag."""
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    try:
        x = float(v)
        if math.isfinite(x):
            return min(1.0, max(0.0, x))
    except (TypeError, ValueError):
        pass
    return 1.0 if _flag(v) else 0.0


def item_credits(rows: list[dict[str, Any]]) -> dict[str, float]:
    """Credit per item (see the module docstring); items without any scored row are left out."""
    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by[str(r.get("item", r.get("item_id", "item_0")))].append(r)
    out: dict[str, float] = {}
    for item, rs in by.items():
        marked = [r for r in rs if r.get("item_correct") is not None and r.get("item_correct") != ""]
        if marked:
            out[item] = _credit(marked[-1]["item_correct"])
            continue
        last = max(int(_num(r.get("round")) or 0) for r in rs)
        scored = [r for r in rs if int(_num(r.get("round")) or 0) == last and r.get("correct") is not None and r.get("correct") != ""]
        if scored:
            out[item] = sum(1.0 for r in scored if _flag(r["correct"])) / len(scored)
    return out


def trace_resources(rows: list[dict[str, Any]]) -> dict[str, Any]:
    v = resource_vector([dict(r, item=str(r.get("item", r.get("item_id", "item_0"))), round=int(_num(r.get("round")) or 0)) for r in rows])
    norm = [dict(r, item=str(r.get("item", r.get("item_id", "item_0"))), round=int(_num(r.get("round")) or 0)) for r in rows]
    return {"r_token": v["r_token"], "r_call": v["r_call"], "r_latency_critical": critical_path_latency(norm), "r_scaff": v["r_scaff"], "r_round": v["r_round"], "r_sample": v["r_sample"],
            "rung": classify_baseline(v)}


def ratio(c: float | None, b: float | None) -> float | None:
    if c is None or b is None:
        return None
    if b == 0:
        return 1.0 if c == 0 else None
    return c / b


def paired_interval(diffs: list[float]) -> tuple[float, float, float]:
    n = len(diffs)
    mean = sum(diffs) / n
    if n < 2:
        return mean, float("nan"), float("nan")
    var = sum((d - mean) ** 2 for d in diffs) / (n - 1)
    se = math.sqrt(var / n)
    return mean, mean - 1.96 * se, mean + 1.96 * se


def verdict(delta: float | None, lo: float | None, hi: float | None, rho_token: float | None, n_shared: int, tol: float, margin: float, min_items: int = 20) -> dict[str, str]:
    if n_shared < 2 or delta is None or lo is None or hi is None or math.isnan(lo) or math.isnan(hi):
        return {"label": "INCONCLUSIVE", "reason": "fewer than two items are present in both traces"}
    if n_shared < min_items:
        return {"label": "INCONCLUSIVE", "reason": "only %d items are present in both traces (at least %d are required to credit or rule out a candidate)" % (n_shared, min_items)}
    if rho_token is None:
        return {"label": "INCONCLUSIVE", "reason": "tokens are missing on one trace, so resource parity cannot be assessed"}
    if lo > 0:
        if rho_token <= 1 + tol:
            return {"label": "CREDITS", "reason": "the candidate is ahead (interval above 0) and used %.2fx the baseline's tokens, so the baseline had at least the candidate's budget" % rho_token}
        return {"label": "INCONCLUSIVE", "reason": "the candidate is ahead but used %.2fx the baseline's tokens; compare at matched compute before crediting it" % rho_token}
    if hi <= margin:
        if rho_token >= 1 / (1 + tol):
            return {"label": "RULES OUT", "reason": "an advantage above %.3f is excluded (upper bound %.3f) although the candidate used %.2fx the baseline's tokens" % (margin, hi, rho_token)}
        return {"label": "INCONCLUSIVE", "reason": "no advantage was found, but the candidate used only %.2fx the baseline's tokens, so it was short of resources" % rho_token}
    return {"label": "INCONCLUSIVE", "reason": "the interval [%.3f, %.3f] is too wide to credit or to rule out the candidate (margin %.3f)" % (lo, hi, margin)}


def compare_traces(base_rows: list[dict[str, Any]], cand_rows: list[dict[str, Any]], tol: float = 0.10, margin: float = 0.05, min_items: int = 20) -> dict[str, Any]:
    cb, cc = item_credits(base_rows), item_credits(cand_rows)
    shared = sorted(set(cb) & set(cc))
    rb, rc = trace_resources(base_rows), trace_resources(cand_rows)
    ratios = {a: ratio(rc[a], rb[a]) for a in AXES}
    if shared:
        diffs = [cc[i] - cb[i] for i in shared]
        delta, lo, hi = paired_interval(diffs)
        acc_b, acc_c = sum(cb[i] for i in shared) / len(shared), sum(cc[i] for i in shared) / len(shared)
    else:
        delta = lo = hi = acc_b = acc_c = None
    v = verdict(delta, lo, hi, ratios["r_token"], len(shared), tol, margin, min_items)
    clean = lambda x: None if (x is None or (isinstance(x, float) and math.isnan(x))) else x  # noqa: E731
    return {
        "schema": SCHEMA,
        "parameters": {"tol": tol, "margin": margin, "min_items": min_items},
        "baseline": {"n_items": len({str(r.get("item", r.get("item_id", "item_0"))) for r in base_rows}), "n_records": len(base_rows), "resources": rb},
        "candidate": {"n_items": len({str(r.get("item", r.get("item_id", "item_0"))) for r in cand_rows}), "n_records": len(cand_rows), "resources": rc},
        "shared_items": len(shared),
        "accuracy": {"baseline": acc_b, "candidate": acc_c, "delta": clean(delta), "ci_low": clean(lo), "ci_high": clean(hi), "method": "paired normal approximation, 95%"},
        "ratios": ratios,
        "verdict": v,
    }


def _f(x: Any, d: int = 3) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else ("%." + str(d) + "f") % x


def to_markdown(rep: dict[str, Any]) -> str:
    b, c, a, r = rep["baseline"], rep["candidate"], rep["accuracy"], rep["ratios"]
    names = {"r_token": "tokens per item", "r_call": "calls per item", "r_latency_critical": "critical-path latency (s per item)", "r_scaff": "scaffold or tool rows per item"}
    lines = ["# PACE comparison: baseline vs candidate", "",
             "**Verdict: %s.** %s." % (rep["verdict"]["label"], rep["verdict"]["reason"]), "",
             "Accuracy on the %d shared items: baseline %s, candidate %s, gap %s (95%% interval [%s, %s], %s)." % (rep["shared_items"], _f(a["baseline"]), _f(a["candidate"]), _f(a["delta"]), _f(a["ci_low"]), _f(a["ci_high"]), a["method"]), "",
             "| resource axis | baseline | candidate | candidate / baseline |", "|---|---:|---:|---:|"]
    for k in AXES:
        lines.append("| %s | %s | %s | %s |" % (names[k], _f(b["resources"][k], 2), _f(c["resources"][k], 2), _f(r[k], 2)))
    lines += ["", "Baseline rung: %s (%d items, %d records). Candidate rung: %s (%d items, %d records)." % (b["resources"]["rung"], b["n_items"], b["n_records"], c["resources"]["rung"], c["n_items"], c["n_records"]),
              "Parity tolerance %.2f, smallest advantage of interest %.3f, at least %d shared items." % (rep["parameters"]["tol"], rep["parameters"]["margin"], rep["parameters"]["min_items"]), ""]
    return "\n".join(lines)


def _tex(s: str) -> str:
    return str(s).replace("\\", "\\textbackslash{}").replace("_", "\\_").replace("%", "\\%").replace("&", "\\&").replace("#", "\\#").replace("$", "\\$")


def to_latex(rep: dict[str, Any]) -> str:
    b, c, a, r = rep["baseline"]["resources"], rep["candidate"]["resources"], rep["accuracy"], rep["ratios"]
    rows = [("Tokens per item", "r_token", 1), ("Calls per item", "r_call", 2), ("Critical-path latency (s per item)", "r_latency_critical", 2), ("Scaffold or tool rows per item", "r_scaff", 2)]
    body = "\n".join("%s & %s & %s & %s \\\\" % (_tex(n), _f(b[k], d), _f(c[k], d), _f(r[k], 2)) for n, k, d in rows)
    return ("%% PACE comparison (pace compare)\n\\begin{table}[t]\n\\centering\n\\footnotesize\n\\caption{PACE comparison on %d shared items: accuracy %s (baseline) against %s (candidate), gap %s [%s, %s]. Verdict: %s.}\n"
            "\\begin{tabular}{@{}lrrr@{}}\n\\toprule\nAxis & Baseline & Candidate & Ratio \\\\\n\\midrule\n%s\n\\bottomrule\n\\end{tabular}\n\\end{table}\n") % (
        rep["shared_items"], _f(a["baseline"]), _f(a["candidate"]), _f(a["delta"]), _f(a["ci_low"]), _f(a["ci_high"]), _tex(rep["verdict"]["label"]), body)
