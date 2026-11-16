"""Export a PACE compute block in a form that sits inside a rollout card (Masters, Liu and Albrecht 2026, arXiv:2605.12131).

What the rollout-card paper specifies (its Appendix E): a card is a logical directory with manifest.json, five append-only JSONL streams (events, nodes, edges,
annotations, mutations) and optional blobs; a card lists the reporting rules behind every reported number, each with a name, an implementation or version,
a configuration, input streams, an output target and a drops manifest; and new metadata goes into annotations.jsonl under a namespace. The paper has no dedicated
compute section.

What this module does: it maps the PACE resource vector R and the frontier gap onto those two extension points, without claiming more.
  * `annotations`: rows in the annotations-stream schema (target_type, target_id, namespace, sequence, payload, created_at) with namespace "pace.compute",
    one row for the MAS resource vector, one for the SAS vector and ratios (if a baseline is present), one for the frontier-gap result;
  * `reporting_rules`: one entry for the frontier-gap rule with its configuration and a drops manifest (fields read, structures collapsed, loss classes).
Limits, repeated in every export: this is a compute block, not a complete rollout card (no events, nodes or edges are written); the manifest key names are not
listed in the rollout-card paper, so none are invented here; and the output has not been checked with the reference validator (ERGON), which is not
installed here. Nothing is estimated: a dimension that the log does not report stays null.
Formats: JSON, YAML (written by a small emitter, no dependency) and a one-page LaTeX block.
"""
from __future__ import annotations

import datetime
import json
from typing import Any, Dict, List, Optional

SPEC = "arXiv:2605.12131"
NAMESPACE = "pace.compute"
DIMENSIONS = ("r_reason", "r_token", "r_cost", "r_lat", "r_sample", "r_sys")
DIM_LABEL = {"r_reason": "thinking tokens", "r_token": "total tokens", "r_cost": "cost (USD)", "r_lat": "latency (s)", "r_sample": "independent samples", "r_sys": "tool calls"}
LIMITS = ("A compute block, not a complete rollout card: no events, nodes or edges are included. Manifest key names are not specified in the rollout-card paper and "
          "are not invented here. Not checked with the reference validator.")


def build_block(rep: dict, run_id: str = "run", created_at: Optional[str] = None, version: str = "0.1") -> Dict[str, Any]:
    """Build the compute block from a `pace.build_report` result. `created_at` defaults to the current UTC time (ISO 8601)."""
    when = created_at or datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    rc = rep.get("resource_card") or {}
    g = rep["frontier_gap"]
    rows: List[dict] = []

    def add(payload: dict) -> None:
        rows.append({"target_type": "run", "target_id": run_id, "namespace": NAMESPACE, "sequence": len(rows) + 1, "payload": payload, "created_at": when})
    add({"kind": "resource_vector", "system": rep.get("system", "mas"), "unit": "per item (mean)", "dimensions": {d: (rc.get("mas_per_item") or {}).get(d) for d in DIMENSIONS}})
    if rc.get("sas_per_item") is not None:
        add({"kind": "resource_vector", "system": "sas", "unit": "per item (mean)", "dimensions": {d: rc["sas_per_item"].get(d) for d in DIMENSIONS}})
        add({"kind": "ratios_mas_over_sas", "dimensions": {d: rc["ratios_mas_over_sas"].get(d) for d in DIMENSIONS},
             "control_states": rc.get("control_states"), "note": "null: not reported by a side, or 0/0"})
    add({"kind": "frontier_gap", "estimate": g["gap"], "ci95": [g["ci_low"], g["ci_high"]], "interval": "paired bootstrap over items", "n_items": g["n_items"],
         "system_accuracy": g["system_accuracy"], "frontier_accuracy_at_system_tokens": g["frontier_at_system_tokens"], "system_mean_tokens": g["system_mean_tokens"],
         "range_status": g["range_status"], "greedy_accuracy": rep.get("greedy_accuracy"), "pool_k": rep["pool_k"]})
    from . import __version__
    rule = {"name": "pace.frontier_gap", "implementation": "pace %s (pace.frontier.frontier_gap)" % __version__,
            "configuration": {"n_boot": g["n_boot"], "pool_k": rep["pool_k"], "tokens": "prompt plus completion tokens of every call of the item",
                              "frontier": "isotonic (pool-adjacent-violators) self-consistency accuracy at the system's mean tokens"},
            "input_streams": ["per-call usage log (pace run log)", "greedy and sampled answer pool (pace baseline)"],
            "output_target": "annotations.jsonl, namespace %s" % NAMESPACE,
            "drops_manifest": {"fields_read": ["item id", "correct", "prompt_tokens", "completion_tokens", "latency"],
                               "collapsed": ["per-call records summed to per-item totals", "agents and rounds pooled"],
                               "loss_classes": ["message content not read", "agent identity erased", "round structure erased", "items without a complete pool dropped (%d)" % rep.get("pool_items_dropped_incomplete", 0),
                                                "calls without a usage block not counted (%d)" % rep.get("system_calls_missing_usage", 0)]}}
    return {"format": "cme-compute-block", "version": version, "targets": "rollout card (%s), annotations namespace and reporting-rule registry" % SPEC, "limits": LIMITS,
            "annotations": rows, "reporting_rules": [rule]}


def _scalar(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    s = str(v)
    return json.dumps(s) if (not s or s != s.strip() or any(c in s for c in ':#{}[],&*!|>\'"%@`\n') or s.lower() in ("null", "true", "false", "yes", "no")
                             or s[0] in "-?0123456789") else s


def to_yaml(obj: Any, indent: int = 0) -> str:
    """Minimal YAML emitter for nested dicts, lists and scalars (block style)."""
    pad = "  " * indent
    if isinstance(obj, dict):
        if not obj:
            return pad + "{}\n"
        out = ""
        for k, v in obj.items():
            if isinstance(v, (dict, list)) and v:
                out += "%s%s:\n%s" % (pad, k, to_yaml(v, indent + 1))
            else:
                out += "%s%s: %s\n" % (pad, k, "{}" if isinstance(v, dict) else "[]" if isinstance(v, list) else _scalar(v))
        return out
    if isinstance(obj, list):
        out = ""
        for v in obj:
            if isinstance(v, (dict, list)) and v:
                body = to_yaml(v, indent + 1)
                out += "%s- %s" % (pad, body[len(pad) + 2:])
            else:
                out += "%s- %s\n" % (pad, _scalar(v))
        return out
    return pad + _scalar(obj) + "\n"


def _tex(s: str) -> str:
    bs = chr(92)
    return s.replace(bs, "").replace("_", bs + "_").replace("%", bs + "%").replace("&", bs + "&").replace("#", bs + "#")


def to_latex(block: dict, title: str = "PACE compute block") -> str:
    """One-page LaTeX block: resource vector (MAS, SAS, ratio) and the frontier-gap line. Null cells print n/a."""
    bs = chr(92)
    ann = {a["payload"]["kind"] + ":" + str(a["payload"].get("system", "")): a["payload"] for a in block["annotations"]}
    mas = next(p for p in (a["payload"] for a in block["annotations"]) if p["kind"] == "resource_vector")
    sas = next((a["payload"] for a in block["annotations"] if a["payload"]["kind"] == "resource_vector" and a["payload"]["system"] == "sas"), None)
    rat = next((a["payload"] for a in block["annotations"] if a["payload"]["kind"] == "ratios_mas_over_sas"), None)
    gap = next(a["payload"] for a in block["annotations"] if a["payload"]["kind"] == "frontier_gap")

    def f(v, nd=3):
        return "n/a" if v is None else ("inf" if v == float("inf") else ("%.0f" % v if abs(v) >= 100 else "%.*g" % (nd, v)))
    lines = [bs + "begin{table}[t]", bs + "centering", bs + "small",
             bs + "caption{" + _tex(title) + " (namespace " + bs + "texttt{" + _tex(NAMESPACE) + "}). Per-item means from the run log; n/a: not reported by the log. "
             "Compute block for a rollout card (" + SPEC.replace("arXiv:", "arXiv:") + "), not a complete card.}",
             bs + "label{tab:cme_compute_block}", bs + "begin{tabular}{lrrr}", bs + "toprule", "Dimension & " + _tex(mas["system"].upper()) + " & SAS & Ratio " + bs + bs, bs + "midrule"]
    for d in DIMENSIONS:
        lines.append("%s (%s) & %s & %s & %s %s" % (_tex(d), _tex(DIM_LABEL[d]), f(mas["dimensions"][d]), f(sas["dimensions"][d]) if sas else "n/a", f(rat["dimensions"][d]) if rat else "n/a", bs + bs))
    lines += [bs + "midrule",
              bs + "multicolumn{4}{l}{Frontier gap $%+.3f$, 95%% paired bootstrap interval [$%+.3f$, $%+.3f$] over %d items; frontier at the system's mean tokens %.3f (%s).} %s" % (
                  gap["estimate"], gap["ci95"][0], gap["ci95"][1], gap["n_items"], gap["frontier_accuracy_at_system_tokens"], _tex(gap["range_status"]), bs + bs),
              bs + "bottomrule", bs + "end{tabular}", bs + "end{table}"]
    return "\n".join(lines).replace("95%", "95" + bs + "%") + "\n"


def write_block(rep: dict, prefix: str, run_id: str = "run") -> List[str]:
    """Write PREFIX.json, PREFIX.yaml and PREFIX.tex; return the paths."""
    block = build_block(rep, run_id)
    paths = []
    for ext, text in (("json", json.dumps(block, indent=2) + "\n"), ("yaml", to_yaml(block)), ("tex", to_latex(block))):
        p = "%s.%s" % (prefix, ext)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        paths.append(p)
    return paths
