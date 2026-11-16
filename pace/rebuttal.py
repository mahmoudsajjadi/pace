"""Nine-column rebuttal table: Study | Benchmark | Model | MA configuration | Baseline rung | MA acc | Baseline acc | Raw gap | Compute-normalized gap.

Two sources:
  * the literature contrasts (outputs/baseline_tier_contrasts.csv: study, category = rung A/B/C, baseline, key 'Study|bench|model|arm',
    p_base, p_mas): one row per (configuration, baseline). Raw gap = MA acc - baseline acc. Compute-normalized gap = MA acc minus the
    strongest single-agent baseline reported for the same configuration (the highest baseline accuracy over its rungs), so it equals the raw
    gap when the row already uses the strongest baseline and is lower when a stronger one exists. It is a within-study comparison, not a
    frontier estimate.
  * a `pace report` run: one row; rung from the baseline classifier (the greedy arm is rung A), raw gap against greedy, and the
    compute-normalized gap is the frontier gap at the system's measured tokens.
Unreported cells print as n/a.
"""

from __future__ import annotations

import csv
import re

COLUMNS = [
    "Study",
    "Benchmark",
    "Model",
    "MA configuration",
    "Baseline rung",
    "MA acc",
    "Baseline acc",
    "Raw gap",
    "Compute-normalized gap",
]


def _f(x: float | None, signed: bool = False) -> str:
    if x is None:
        return "n/a"
    return ("%+.3f" if signed else "%.3f") % x


def rows_from_contrasts(path: str, study: str | None = None) -> list[dict[str, str]]:
    raw = list(csv.DictReader(open(path, encoding="utf-8")))
    best: dict[str, float] = {}
    for r in raw:
        best[r["key"]] = max(best.get(r["key"], -1.0), float(r["p_base"]))
    out = []
    for r in raw:
        if study and r["study"] != study:
            continue
        _, bench, model, arm = r["key"].split("|", 3)
        pb, pm = float(r["p_base"]), float(r["p_mas"])
        out.append(
            {
                "Study": r["study"],
                "Benchmark": bench,
                "Model": model,
                "MA configuration": arm,
                "Baseline rung": r["category"],
                "MA acc": _f(pm),
                "Baseline acc": _f(pb),
                "Raw gap": _f(pm - pb, True),
                "Compute-normalized gap": _f(pm - best[r["key"]], True),
            }
        )
    return out


def row_from_report(
    rep: dict, benchmark: str = "n/a", model: str = "n/a", config: dict | None = None
) -> dict[str, str]:
    """One row for a `pace report` result. `config` describes the baseline (default: the greedy arm, rung A)."""
    from mae_eval.classifier import classify_baseline_rung

    g = rep["frontier_gap"]
    rung = classify_baseline_rung(config or {"n_samples": 1})
    ga = rep.get("greedy_accuracy")
    return {
        "Study": "this run",
        "Benchmark": benchmark,
        "Model": model,
        "MA configuration": rep.get("system", "n/a"),
        "Baseline rung": rung,
        "MA acc": _f(g["system_accuracy"]),
        "Baseline acc": _f(ga),
        "Raw gap": _f(None if ga is None else g["system_accuracy"] - ga, True),
        "Compute-normalized gap": _f(g["gap"], True)
        + " [%s, %s]" % (_f(g["ci_low"], True), _f(g["ci_high"], True)),
    }


def to_markdown(rows: list[dict[str, str]]) -> str:
    lines = ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
    lines += ["| " + " | ".join(r[c] for c in COLUMNS) + " |" for r in rows]
    return "\n".join(lines) + "\n"


def _tex(s: str) -> str:
    for a, b in (("&", "\\&"), ("%", "\\%"), ("_", "\\_"), ("#", "\\#"), ("$", "\\$")):
        s = s.replace(a, b)
    return s


def _signed(s: str) -> str:
    return re.sub(r"([+-])(\d)", r"$\1$\2", s)


def to_latex(
    rows: list[dict[str, str]],
    caption: str = "Contrasts by baseline rung.",
    label: str = "tab:rebuttal",
) -> str:
    head = " & ".join(c for c in COLUMNS) + r" \\"
    body = [
        " & ".join(
            _signed(_tex(r[c]))
            if c in ("Raw gap", "Compute-normalized gap")
            else _tex(r[c])
            for c in COLUMNS
        )
        + r" \\"
        for r in rows
    ]
    return (
        "\n".join(
            [
                r"\begin{table}[t]",
                r"\centering",
                r"\scriptsize",
                r"\caption{%s}" % caption,
                r"\label{%s}" % label,
                r"\resizebox{\textwidth}{!}{%",
                r"\begin{tabular}{lllllrrrr}",
                r"\toprule",
                head,
                r"\midrule",
            ]
            + body
            + [r"\bottomrule", r"\end{tabular}}", r"\end{table}"]
        )
        + "\n"
    )


def audit_contrasts_noise_band(rows: list[dict], phi: float = 0.50) -> dict:
    """Summarize paired-binomial noise bands, effect sizes, and baseline cells."""
    import math

    if not 0 <= phi <= 1:
        raise ValueError("phi must be between 0 and 1")
    details = []
    counts = {
        "below_-1.96_se": 0,
        "within_+-1.96_se": 0,
        "above_+1.96_se": 0,
        "below_-1.0_se": 0,
        "within_+-1.0_se": 0,
        "above_+1.0_se": 0,
    }
    for row in rows:
        pm, pb, n = float(row["p_mas"]), float(row["p_base"]), float(row.get("n", 1))
        vm, vb = pm * (1 - pm), pb * (1 - pb)
        se = math.sqrt(max(0.0, (vm + vb - 2 * phi * math.sqrt(max(0.0, vm * vb))) / n))
        delta = pm - pb
        for scale, low, middle, high in (
            (1.96, "below_-1.96_se", "within_+-1.96_se", "above_+1.96_se"),
            (1.0, "below_-1.0_se", "within_+-1.0_se", "above_+1.0_se"),
        ):
            if delta < -scale * se:
                counts[low] += 1
            elif delta > scale * se:
                counts[high] += 1
            else:
                counts[middle] += 1
        h = 2 * math.asin(math.sqrt(max(0.0, min(1.0, pm)))) - 2 * math.asin(
            math.sqrt(max(0.0, min(1.0, pb)))
        )
        p11 = min(pm, pb)
        p10, p01, p00 = pm - p11, pb - p11, 1 - pm - pb + p11
        if p10 * p01 == 0:
            log_or = float("inf") if p11 * p00 > 0 else 0.0
        else:
            log_or = math.log(max(1e-300, (p11 * p00) / (p10 * p01)))
        phi_max = 0.0 if math.isinf(log_or) else math.exp(-abs(log_or) / 2)
        details.append(
            {
                "delta": delta,
                "se_delta": se,
                "cohens_h": h,
                "log_or": log_or,
                "phi_max": phi_max,
                "phi_binds": phi > phi_max,
            }
        )
    cells = {}
    for row in rows:
        key = tuple(
            row.get(name, "") for name in ("study", "benchmark", "model", "category")
        )
        cell = cells.setdefault(key, {"n": 0, "p_mas": [], "p_base": []})
        cell["n"] += int(row.get("n", 1))
        cell["p_mas"].append(float(row["p_mas"]))
        cell["p_base"].append(float(row["p_base"]))
    summaries = [
        {
            "study": key[0],
            "benchmark": key[1],
            "model": key[2],
            "category": key[3],
            "n": value["n"],
            "p_mas": sum(value["p_mas"]) / len(value["p_mas"]),
            "p_base": sum(value["p_base"]) / len(value["p_base"]),
        }
        for key, value in cells.items()
    ]
    return {
        "phi": phi,
        "n_contrasts": len(rows),
        "counts": counts,
        "contrasts": details,
        "phi_clamp_count": sum(item["phi_binds"] for item in details),
        "baseline_cells": summaries,
    }
