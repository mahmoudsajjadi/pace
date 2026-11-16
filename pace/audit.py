"""pace audit: a one-screen diagnostic card for a multi-agent evaluation (standard library plus mae_eval).

    pace audit run_trace.jsonl                      # a run log with "mas" and "sas" calls: measured MAS/SAS resource ratios and parity
    pace audit run_trace.jsonl --baseline-config sas.json   # plus the rung of the single-agent baseline (keys: code/mae_eval/classifier.py)
    pace audit sas.json                             # a baseline configuration only: its rung and whether a matched resource is declared

Badge rules (stated on the card):
  PASS: COMPUTE-MATCHED   a log was given, token parity holds within the tolerance (r_token ratio within 1 +/- tolerance), and, if a baseline configuration
                          was given, its rung is C or D; or only a configuration was given and its rung is C (rule R2) or D.
  WARNING: BASELINE NOT COMPUTE-MATCHED   anything else: parity violated or not measurable, or the baseline is rung A or B, or rung C with the matching unverified (R3).
Rung A or B does not make a baseline wrong; it means the comparison does not separate coordination from extra computation. Nothing here estimates tokens.
"""
from __future__ import annotations

import json
import math
from typing import Dict, Optional

BIBTEX = """@unpublished{cme2026,
  title  = {More Agents, More Samples, or More Thinking? Untangling Coordination, Ensembling, and Test-Time Compute in Multi-Agent {LLMs}},
  author = {Sajjadi Mohammadabadi, Seyed Mahmoud},
  year   = {2026},
  note   = {Manuscript in preparation}
}"""


def _fmt(r: Optional[float]) -> str:
    if r is None:
        return "n/a"
    return "inf" if math.isinf(r) else "%.2f\u00d7" % r


def load_input(path: str):
    """Return ('config', dict) for a single JSON object without a 'system' key, else ('log', {system: [records]})."""
    text = open(path, encoding="utf-8").read()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "system" not in obj:
            return "config", obj
    except json.JSONDecodeError:
        pass
    from mae_eval.cli import TraceError, load_trace
    recs = []
    for no, line in enumerate(text.splitlines(), 1):
        if line.strip():
            r = json.loads(line)
            if "correct" in r and "prompt_tokens" not in r:   # a per-item result line written by pace.log_result or by hand
                continue
            recs.append({k: v for k, v in r.items() if v is not None})   # null = unreported (proxy and wrap logs): treat as absent, never as 0 by guess
    import tempfile, os
    fd, tmp = tempfile.mkstemp(suffix=".jsonl")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("\n".join(json.dumps(r) for r in recs) + "\n")
        try:
            return "log", load_trace(tmp)
        except TraceError as e:
            raise ValueError(str(e))
    finally:
        os.unlink(tmp)


def audit(path: str, baseline_config: Optional[str] = None, tolerance: float = 0.05, price_in: Optional[float] = None, price_out: Optional[float] = None) -> Dict:
    from mae_eval.auditor import EvaluationAuditor
    from mae_eval.classifier import classify_with_reason
    from mae_eval.cli import session_from_records
    from mae_eval.tracker import ResourceTracker
    kind, data = load_input(path)
    card: Dict = {"input": kind, "tolerance": tolerance, "rung": None, "rule": None, "rung_reason": None, "ratios": None, "parity": None, "notes": []}
    cfg = None
    if kind == "config":
        cfg = data
    elif baseline_config:
        cfg = json.load(open(baseline_config, encoding="utf-8"))
    if cfg is not None:
        card["rung"], card["rule"], card["rung_reason"] = classify_with_reason(cfg)
    if kind == "log":
        if "mas" not in data or "sas" not in data:
            card["notes"].append("the log needs both 'mas' and 'sas' calls to compute ratios; systems found: %s" % ", ".join(sorted(data)))
        else:
            priced = price_in is not None and price_out is not None
            tracker = ResourceTracker("model", "cme-audit")
            if priced:
                tracker.register_pricing(price_in, price_out)
            vec = {k: session_from_records(v, tracker).get_resource_vector(allow_missing_pricing=not priced) for k, v in data.items() if k in ("mas", "sas")}
            aud = EvaluationAuditor(vec["mas"], vec["sas"])
            r = aud.ratios()
            card["ratios"] = {"r_token": r["r_token"], "r_lat": r["r_lat"], "r_cost": r["r_cost"]}
            tok = r["r_token"]
            card["parity"] = bool(tok is not None and not math.isinf(tok) and abs(tok - 1.0) <= tolerance)
            if not priced:
                card["notes"].append("no prices given: cost ratio not computed")
    elif cfg is not None:
        card["notes"].append("a configuration alone has no measured tokens: no resource ratios")
    if card["rung"] is None:
        card["notes"].append("baseline rung not classified: pass --baseline-config or a configuration file")
    rung, rule = card["rung"], card["rule"]
    if kind == "log":
        ok = bool(card["parity"]) and (rung in (None, "C", "D"))
        if rung is None:
            ok = False   # parity alone with an unknown baseline is not enough to call the comparison matched
    else:
        ok = rung == "D" or (rung == "C" and rule == "R2")
    card["badge"] = "PASS: COMPUTE-MATCHED" if ok else "WARNING: BASELINE NOT COMPUTE-MATCHED"
    card["ok"] = ok
    return card


def render(card: Dict, ascii_only: bool = False) -> str:
    w = 66
    line = "\u2500" * w
    out = ["\u250c" + line + "\u2510"]

    def row(s=""):
        import textwrap
        for part in textwrap.wrap(s, w - 3, subsequent_indent="  ", drop_whitespace=False)[:] or [""]:
            out.append("\u2502 " + part.ljust(w - 1) + "\u2502")
    row("PACE audit")
    out.append("\u251c" + line + "\u2524")
    if card["rung"]:
        cat = {"A": "Category A (single greedy pass)", "B": "Category B (sampled, unmatched tokens)", "C": "Category C (resource-matched or test-time scaling)",
               "D": "Category D (budget sweep)"}[card["rung"]]
        row("Baseline rung   : %s [%s]" % (cat, card["rule"]))
        row("                  %s" % card["rung_reason"])
    else:
        row("Baseline rung   : not classified")
    r = card["ratios"]
    if r:
        row("MAS / SAS       : R_token %s   R_lat %s   R_cost %s" % (_fmt(r["r_token"]), _fmt(r["r_lat"]), _fmt(r["r_cost"])))
        row("Token parity    : %s (tolerance %.0f%%)" % ("holds" if card["parity"] else "violated", 100 * card["tolerance"]))
    else:
        row("MAS / SAS       : not available")
    row()
    row("[%s]" % card["badge"])
    for n in card["notes"]:
        row("note: " + n)
    out.append("\u2514" + line + "\u2518")
    out.append("")
    out.append("To cite (BibTeX; the manuscript is in preparation):")
    out.append(BIBTEX)
    text = "\n".join(out)
    if ascii_only:
        for u, c in (("\u250c", "+"), ("\u2510", "+"), ("\u2514", "+"), ("\u2518", "+"), ("\u251c", "+"), ("\u2524", "+"), ("\u2500", "-"), ("\u2502", "|"), ("\u00d7", "x")):
            text = text.replace(u, c)
    return text
