"""Load a confirmatory cell (one model x one task) and estimate frontier gaps per strategy.

A cell directory holds calls.jsonl (every call) and results.jsonl (one row per strategy x item). The pool frontier is rebuilt from the
cached pool calls with the same scorer used at run time, so re-scoring never needs a model. Correctness of a pool sample is mapped to
the label 'G' (wrong answers keep their normalised text) so plurality voting uses the scorer's notion of correct.

Estimand (docs/PREREGISTRATION.md section 5): gap(s) = accuracy(s) - F(mean tokens of s), F the isotonic self-consistency frontier,
with a paired bootstrap over items. `pool="views"` builds the frontier from the independent split-evidence agents (S2v) instead.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

import numpy as np

from . import experiment as E
from . import tasks as T
from .frontier import Pool, frontier_curve, frontier_gap, pav_increasing


def read_results(cell_dir: str) -> Dict[str, Dict[str, dict]]:
    out: Dict[str, Dict[str, dict]] = {}
    p = os.path.join(cell_dir, "results.jsonl")
    if os.path.exists(p):
        for l in open(p, encoding="utf-8"):
            if l.strip():
                r = json.loads(l)
                out.setdefault(r["strategy"], {})[r["item"]] = r
    return out


def build_pool(store: E.Store, model: str, items: List[dict], pool: str = "pool", k: int = 16) -> Pool:
    """Pool of per-item sampled answers and token counts. pool='pool' uses the 16 full-evidence samples; 'views' the 5 split-evidence agents."""
    pitems = {}
    for it in items:
        if it["kind"] == "code":
            continue
        keys = ["pool|%s|%s|%d" % (model, it["id"], i) for i in range(k)] if pool == "pool" else ["r1v|%s|%s|%d" % (model, it["id"], i) for i in range(k)]
        recs = [store.d.get(x) for x in keys]
        if any(r is None or r.get("prompt_tokens") is None or r.get("completion_tokens") is None for r in recs):
            continue
        pitems[it["id"]] = {"gold": "G", "answers": ["G" if T.score(it, r["text"]) else (E.ans_of(it, r) or "?") + "_wrong" for r in recs],
                            "tokens": [r["prompt_tokens"] + r["completion_tokens"] for r in recs]}
    return Pool(pitems, k) if pitems else None


def cell_gaps(cell_dir: str, model: str, items: List[dict], strategies: Optional[List[str]] = None, pool: str = "pool", k: Optional[int] = None,
              n_boot: int = 2000, n_perm: int = 100, seed: int = 0, tokens: str = "total") -> dict:
    """Frontier, per-strategy accuracy, mean tokens and gap with a bootstrap interval. tokens='completion' is the sensitivity analysis."""
    store = E.Store(os.path.join(cell_dir, "calls.jsonl"))
    k = k or (16 if pool == "pool" else 5)
    P = build_pool(store, model, items, pool, k)
    if P is None:
        return {"error": "no complete pool in %s" % cell_dir}
    if tokens == "completion":   # recompute pool tokens with completion tokens only
        for it in P.items:
            keys = ["pool|%s|%s|%d" % (model, it, i) if pool == "pool" else "r1v|%s|%s|%d" % (model, it, i) for i in range(k)]
            P.items[it]["tokens"] = [store.d[x]["completion_tokens"] for x in keys]
    ids, acc, tok = P.curves(n_perm, seed)
    res = read_results(cell_dir)
    out = {"model": model, "pool": pool, "k": k, "n_pool_items": len(ids), "tokens": tokens, "strategies": {}}
    tk, ak = frontier_curve(acc, tok)
    out["frontier"] = {"tokens": tk.tolist(), "sc_accuracy": ak.tolist(), "isotonic": pav_increasing(ak).tolist()}
    for s, rows in sorted(res.items()):
        if strategies and s not in strategies:
            continue
        common = [i for i in ids if i in rows]
        if len(common) < 5:
            continue
        pos = {i: n for n, i in enumerate(ids)}
        sel = [pos[i] for i in common]
        use = (lambda r: r["completion_tokens"]) if tokens == "completion" else (lambda r: r["prompt_tokens"] + r["completion_tokens"])
        sc = np.array([float(rows[i]["correct"]) for i in common])
        st = np.array([float(use(rows[i])) for i in common])
        g = frontier_gap(acc[sel], tok[sel], sc, st, n_boot=n_boot, seed=seed)
        g["n_items"] = len(common)
        out["strategies"][s] = g
    return out


def difference_of_gaps(cell_dir: str, model: str, items: List[dict], a: str, b: str, n_boot: int = 2000, seed: int = 0, n_perm: int = 100) -> Optional[dict]:
    """Paired bootstrap of gap(a) - gap(b) on the items both strategies finished (used for H3: S4 versus S3)."""
    store = E.Store(os.path.join(cell_dir, "calls.jsonl"))
    P = build_pool(store, model, items, "pool", 16)
    res = read_results(cell_dir)
    if P is None or a not in res or b not in res:
        return None
    ids, acc, tok = P.curves(n_perm, seed)
    common = [i for i in ids if i in res[a] and i in res[b]]
    if len(common) < 5:
        return None
    pos = {i: n for n, i in enumerate(ids)}
    sel = np.array([pos[i] for i in common])
    sa = np.array([float(res[a][i]["correct"]) for i in common]); ta = np.array([float(res[a][i]["prompt_tokens"] + res[a][i]["completion_tokens"]) for i in common])
    sb = np.array([float(res[b][i]["correct"]) for i in common]); tb = np.array([float(res[b][i]["prompt_tokens"] + res[b][i]["completion_tokens"]) for i in common])
    from .frontier import frontier_at
    rng = np.random.default_rng(seed)
    n = len(common)
    A, T_ = acc[sel], tok[sel]

    def one(ix):
        tk, ak = frontier_curve(A[ix], T_[ix])
        ga = sa[ix].mean() - frontier_at(tk, ak, float(ta[ix].mean()))[0]
        gb = sb[ix].mean() - frontier_at(tk, ak, float(tb[ix].mean()))[0]
        return ga - gb
    est = one(np.arange(n))
    boots = np.array([one(rng.integers(0, n, n)) for _ in range(n_boot)])
    lo, hi = np.quantile(boots, [0.025, 0.975])
    p_two = float(min(1.0, 2 * (min(np.sum(boots <= 0), np.sum(boots >= 0)) + 1) / (n_boot + 1)))   # bootstrap two-sided p for H0: difference = 0
    return {"difference": float(est), "ci_low": float(lo), "ci_high": float(hi), "p_two_sided": p_two, "n_items": n, "a": a, "b": b}


def holm(pvals: Dict[str, float], alpha: float = 0.05) -> Dict[str, dict]:
    """Holm step-down: returns adjusted p-values and rejection flags."""
    order = sorted(pvals, key=pvals.get)
    m = len(order)
    out, running = {}, 0.0
    for i, name in enumerate(order):
        adj = min(1.0, (m - i) * pvals[name])
        running = max(running, adj)
        out[name] = {"p": pvals[name], "p_holm": running, "reject": running < alpha}
    return out


def one_sided_p(boots_gap: np.ndarray) -> float:
    """Bootstrap p-value for H0: gap <= 0 (share of resamples with gap <= 0)."""
    return float((np.sum(boots_gap <= 0) + 1) / (len(boots_gap) + 1))
