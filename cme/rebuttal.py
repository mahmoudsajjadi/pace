"""Nine-column rebuttal table: Study | Benchmark | Model | MA configuration | Baseline rung | MA acc | Baseline acc | Raw gap | Compute-normalized gap.

Two sources:
  * the literature contrasts (outputs/baseline_tier_contrasts.csv: study, category = rung A/B/C, baseline, key 'Study|bench|model|arm',
    p_base, p_mas): one row per (configuration, baseline). Raw gap = MA acc - baseline acc. Compute-normalized gap = MA acc minus the
    strongest single-agent baseline reported for the same configuration (the highest baseline accuracy over its rungs), so it equals the raw
    gap when the row already uses the strongest baseline and is lower when a stronger one exists. It is a within-study comparison, not a
    frontier estimate.
  * a `cme report` run: one row; rung from the baseline classifier (the greedy arm is rung A), raw gap against greedy, and the
    compute-normalized gap is the frontier gap at the system's measured tokens.
Unreported cells print as n/a.
"""
from __future__ import annotations

import csv
import re
from typing import Dict, List, Optional

COLUMNS = ["Study", "Benchmark", "Model", "MA configuration", "Baseline rung", "MA acc", "Baseline acc", "Raw gap", "Compute-normalized gap"]


def _f(x: Optional[float], signed: bool = False) -> str:
    if x is None:
        return "n/a"
    return ("%+.3f" if signed else "%.3f") % x


def rows_from_contrasts(path: str, study: Optional[str] = None) -> List[Dict[str, str]]:
    raw = list(csv.DictReader(open(path, encoding="utf-8")))
    best: Dict[str, float] = {}
    for r in raw:
        best[r["key"]] = max(best.get(r["key"], -1.0), float(r["p_base"]))
    out = []
    for r in raw:
        if study and r["study"] != study:
            continue
        _, bench, model, arm = r["key"].split("|", 3)
        pb, pm = float(r["p_base"]), float(r["p_mas"])
        out.append({"Study": r["study"], "Benchmark": bench, "Model": model, "MA configuration": arm, "Baseline rung": r["category"],
                    "MA acc": _f(pm), "Baseline acc": _f(pb), "Raw gap": _f(pm - pb, True), "Compute-normalized gap": _f(pm - best[r["key"]], True)})
    return out


def row_from_report(rep: dict, benchmark: str = "n/a", model: str = "n/a", config: Optional[dict] = None) -> Dict[str, str]:
    """One row for a `cme report` result. `config` describes the baseline (default: the greedy arm, rung A)."""
    from mae_eval.classifier import classify_baseline_rung
    g = rep["frontier_gap"]
    rung = classify_baseline_rung(config or {"n_samples": 1})
    ga = rep.get("greedy_accuracy")
    return {"Study": "this run", "Benchmark": benchmark, "Model": model, "MA configuration": rep.get("system", "n/a"), "Baseline rung": rung,
            "MA acc": _f(g["system_accuracy"]), "Baseline acc": _f(ga), "Raw gap": _f(None if ga is None else g["system_accuracy"] - ga, True),
            "Compute-normalized gap": _f(g["gap"], True) + " [%s, %s]" % (_f(g["ci_low"], True), _f(g["ci_high"], True))}


def to_markdown(rows: List[Dict[str, str]]) -> str:
    lines = ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
    lines += ["| " + " | ".join(r[c] for c in COLUMNS) + " |" for r in rows]
    return "\n".join(lines) + "\n"


def _tex(s: str) -> str:
    for a, b in (("&", "\\&"), ("%", "\\%"), ("_", "\\_"), ("#", "\\#"), ("$", "\\$")):
        s = s.replace(a, b)
    return s


def _signed(s: str) -> str:
    return re.sub(r"([+-])(\d)", r"$\1$\2", s)


def to_latex(rows: List[Dict[str, str]], caption: str = "Contrasts by baseline rung.", label: str = "tab:rebuttal") -> str:
    head = " & ".join(c for c in COLUMNS) + r" \\"
    body = [" & ".join(_signed(_tex(r[c])) if c in ("Raw gap", "Compute-normalized gap") else _tex(r[c]) for c in COLUMNS) + r" \\"
            for r in rows]
    return "\n".join([r"\begin{table}[t]", r"\centering", r"\scriptsize", r"\caption{%s}" % caption, r"\label{%s}" % label, r"\resizebox{\textwidth}{!}{%",
                      r"\begin{tabular}{lllllrrrr}", r"\toprule", head, r"\midrule"] + body + [r"\bottomrule", r"\end{tabular}}", r"\end{table}"]) + "\n"
