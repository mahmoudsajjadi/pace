"""cme report: frontier gap, per-item resource card, LaTeX table and vector figure from a baseline pool and a system log.

Inputs
  --pool  baseline cache written by `cme baseline` (greedy + sampled completions per item)
  --logs  JSONL of the system under test: call records (proxy format: system, item, prompt_tokens, completion_tokens, optional
          reasoning_tokens, start, end, cost, tool_calls) and result records {"item", "system", "correct": true|false}
          (a record that has "correct" and no token fields is a result).
The resource card reports per-item means for the system (MAS) and the greedy baseline (SAS) and passes them to mae_eval's auditor.
A ratio is n/a when both sides are 0 or when either side is unreported.
"""
from __future__ import annotations

import json
from typing import Dict, List, Optional

import numpy as np

from mae_eval.auditor import EvaluationAuditor
from mae_eval.vector import DIMENSIONS, ResourceVector

from .baseline import load_pool
from .frontier import frontier_curve, frontier_gap, frontier_at, pav_increasing

OKABE_ITO = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73", "verm": "#D55E00", "grey": "#666666"}


def read_run(path: str, system: str):
    calls: Dict[str, List[dict]] = {}
    results: Dict[str, bool] = {}
    skipped = 0
    for l in open(path, encoding="utf-8"):
        if not l.strip():
            continue
        r = json.loads(l)
        if r.get("system", system) != system:
            continue
        if "correct" in r and "prompt_tokens" not in r:
            results[str(r["item"])] = bool(r["correct"])
        elif r.get("prompt_tokens") is None or r.get("completion_tokens") is None:
            skipped += 1  # usage missing: counted, never guessed
        else:
            calls.setdefault(str(r.get("item", "")), []).append(r)
    return calls, results, skipped


def _mean(xs: List[Optional[float]]) -> Optional[float]:
    return None if (not xs or any(x is None for x in xs)) else float(sum(xs) / len(xs))


def _vector(per_item: List[List[dict]], price_in: Optional[float], price_out: Optional[float]) -> ResourceVector:
    """Per-item mean resource vector from a list (one entry per item) of call-record lists."""
    tok, reas, cost, lat, samp, sysc = [], [], [], [], [], []
    for calls in per_item:
        tok.append(sum(c["prompt_tokens"] + c["completion_tokens"] for c in calls))
        reas.append(None if any(c.get("reasoning_tokens") is None for c in calls) else sum(c["reasoning_tokens"] for c in calls))
        if price_in is not None and price_out is not None:
            cost.append(sum((c["prompt_tokens"] * price_in + c["completion_tokens"] * price_out) / 1e6 for c in calls))
        elif all(c.get("cost") is not None for c in calls):
            cost.append(sum(c["cost"] for c in calls))
        else:
            cost.append(None)
        if all(c.get("start") is not None and c.get("end") is not None for c in calls):
            lat.append(max(c["end"] for c in calls) - min(c["start"] for c in calls))  # makespan, concurrency-aware
        else:
            lat.append(None if any(c.get("latency") is None for c in calls) else sum(c["latency"] for c in calls))
        samp.append(sum(int(c.get("n_completions", 1)) for c in calls))
        sysc.append(sum(int(c.get("tool_calls", 0)) for c in calls))
    return ResourceVector(r_reason=_mean(reas), r_token=_mean(tok), r_cost=_mean(cost), r_lat=_mean(lat), r_sample=_mean(samp), r_sys=_mean(sysc))


def build_report(pool_path: str, log_path: str, system: str = "mas", price_in: Optional[float] = None, price_out: Optional[float] = None,
                 n_boot: int = 2000, n_perm: int = 100, seed: int = 0, k: Optional[int] = None) -> dict:
    pool, greedy, dropped = load_pool(pool_path, k)
    ids, acc, tok = pool.curves(n_perm, seed)
    calls, results, skipped = read_run(log_path, system)
    common = [i for i in ids if i in results and i in calls]
    if not common:
        raise ValueError("no item has both a pool and a system result; check item ids")
    pos = {i: n for n, i in enumerate(ids)}
    sel = [pos[i] for i in common]
    sys_correct = np.array([float(results[i]) for i in common])
    sys_tokens = np.array([float(sum(c["prompt_tokens"] + c["completion_tokens"] for c in calls[i])) for i in common])
    gap = frontier_gap(acc[sel], tok[sel], sys_correct, sys_tokens, n_boot=n_boot, seed=seed)
    tk, ak = frontier_curve(acc[sel], tok[sel])
    fit = pav_increasing(ak)
    sas_items = [[{"prompt_tokens": greedy[i]["prompt_tokens"], "completion_tokens": greedy[i]["completion_tokens"],
                   "reasoning_tokens": greedy[i].get("reasoning_tokens"), "latency": greedy[i]["latency"]}] for i in common if i in greedy]
    card: dict = {}
    if len(sas_items) == len(common) and all(c[0]["prompt_tokens"] is not None for c in sas_items):
        sas_v = _vector(sas_items, price_in, price_out)
        mas_v = _vector([calls[i] for i in common], price_in, price_out)
        aud = EvaluationAuditor(mas_v, sas_v)
        card = {"mas_per_item": mas_v.to_dict(), "sas_per_item": sas_v.to_dict(), "ratios_mas_over_sas": aud.ratios(),
                "control_states": {d: s.value for d, s in aud.control_states().items()}}
    greedy_acc = float(np.mean([greedy[i]["correct"] for i in common if i in greedy])) if any(i in greedy for i in common) else None
    return {"n_items": len(common), "pool_k": pool.K, "pool_items_dropped_incomplete": dropped, "system_calls_missing_usage": skipped,
            "frontier": {"tokens": tk.tolist(), "sc_accuracy": ak.tolist(), "isotonic": fit.tolist()}, "greedy_accuracy": greedy_acc,
            "frontier_gap": gap, "resource_card": card, "system": system}


def to_latex(rep: dict, caption: str = "Frontier gap and per-item resource card.", label: str = "tab:cme_report") -> str:
    g = rep["frontier_gap"]
    rows = [r"\begin{table}[h]", r"\centering", r"\small", r"\caption{%s}" % caption, r"\label{%s}" % label, r"\begin{tabular}{lrr}", r"\toprule",
            r"Quantity & System & Greedy baseline \\", r"\midrule"]
    rc = rep.get("resource_card") or {}
    for d in DIMENSIONS:
        if rc:
            m, s = rc["mas_per_item"][d], rc["sas_per_item"][d]
            fmt = lambda x: "n/a" if x is None else ("%.4g" % x)
            rows.append(r"%s & %s & %s \\" % (d.replace("_", r"\_"), fmt(m), fmt(s)))
    rows += [r"\midrule", r"Accuracy & %.3f & %s \\" % (g["system_accuracy"], "n/a" if rep["greedy_accuracy"] is None else "%.3f" % rep["greedy_accuracy"]),
             r"Self-consistency frontier at system tokens & \multicolumn{2}{r}{%.3f (%s)} \\" % (g["frontier_at_system_tokens"], g["range_status"]),
             r"Frontier gap (95\%% bootstrap CI) & \multicolumn{2}{r}{$%+.3f$ [$%+.3f$, $%+.3f$]} \\" % (g["gap"], g["ci_low"], g["ci_high"]),
             r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(rows) + "\n"


def plot(rep: dict, out_path: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker
    matplotlib.rcParams["pdf.fonttype"] = 42
    f, g = rep["frontier"], rep["frontier_gap"]
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    ax.plot(f["tokens"], f["sc_accuracy"], "o", color=OKABE_ITO["grey"], ms=3.5, label="Self-consistency, k = 1 to %d" % rep["pool_k"])
    ax.plot(f["tokens"], f["isotonic"], "-", color=OKABE_ITO["blue"], lw=1.6, label="Isotonic frontier")
    if rep["greedy_accuracy"] is not None:
        ax.plot([f["tokens"][0]], [rep["greedy_accuracy"]], "s", color=OKABE_ITO["green"], label="Greedy")
    ax.plot([g["system_mean_tokens"]], [g["system_accuracy"]], "D", color=OKABE_ITO["verm"], label="System (%s)" % rep["system"])
    ax.vlines(g["system_mean_tokens"], g["frontier_at_system_tokens"], g["system_accuracy"], colors=OKABE_ITO["verm"], lw=1.2, linestyles=":")
    ax.set_xscale("log")
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel("Mean tokens per item (prompt + completion)")
    ax.set_ylabel("Accuracy")
    ax.set_title("gap %+.3f [%+.3f, %+.3f]" % (g["gap"], g["ci_low"], g["ci_high"]), fontsize=9)
    ax.legend(fontsize=7, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


OI_CYCLE = ["#D55E00", "#009E73", "#E69F00", "#CC79A7", "#56B4E9", "#F0E442", "#000000"]   # Okabe-Ito, skipping the frontier blue


def frontier_report(pool_path: str, k: Optional[int] = None, n_perm: int = 100, seed: int = 0) -> dict:
    """Self-consistency frontier of a sample pool: points for k = 1..K, isotonic fit, greedy accuracy. No system needed."""
    pool, greedy, dropped = load_pool(pool_path, k)
    ids, acc, tok = pool.curves(n_perm, seed)
    tk, ak = frontier_curve(acc, tok)
    gacc = float(np.mean([greedy[i]["correct"] for i in ids if i in greedy])) if any(i in greedy for i in ids) else None
    return {"n_items": len(ids), "pool_k": pool.K, "pool_items_dropped_incomplete": dropped, "tokens": tk.tolist(), "sc_accuracy": ak.tolist(),
            "isotonic": pav_increasing(ak).tolist(), "greedy_accuracy": gacc}


def system_points(log_path: str) -> List[dict]:
    """Accuracy and mean tokens per item of every system in a run log (systems are the values of the 'system' field)."""
    names = []
    for l in open(log_path, encoding="utf-8"):
        if l.strip():
            s = json.loads(l).get("system")
            if s and s not in names:
                names.append(s)
    out = []
    for s in names:
        calls, results, _ = read_run(log_path, s)
        common = [i for i in results if i in calls]
        if common:
            out.append({"system": s, "accuracy": float(np.mean([results[i] for i in common])), "n_items": len(common),
                        "mean_tokens": float(np.mean([sum(c["prompt_tokens"] + c["completion_tokens"] for c in calls[i]) for i in common]))})
    return out


def plot_frontier(fr: dict, points: List[dict], out_path: str) -> None:
    """Frontier curve with system points (Okabe-Ito palette); .pdf is vector, .png is raster."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker
    matplotlib.rcParams["pdf.fonttype"] = 42
    fig, ax = plt.subplots(figsize=(5.4, 3.5))
    ax.plot(fr["tokens"], fr["sc_accuracy"], "o", color="#666666", ms=3.5, label="self-consistency, k = 1 to %d" % fr["pool_k"])
    ax.plot(fr["tokens"], fr["isotonic"], "-", color="#0072B2", lw=1.6, label="isotonic frontier")
    if fr.get("greedy_accuracy") is not None:
        ax.plot([fr["tokens"][0]], [fr["greedy_accuracy"]], "s", color="#56B4E9", mec="white", label="greedy")
    for i, p in enumerate(points):
        ax.plot([p["mean_tokens"]], [p["accuracy"]], "D", color=OI_CYCLE[i % len(OI_CYCLE)], mec="white", ms=7, label=p["system"])
    ax.set_xscale("log")
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel("Mean tokens per item (prompt + completion)")
    ax.set_ylabel("Accuracy")
    ax.legend(fontsize=7, frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", dpi=200)
    plt.close(fig)
