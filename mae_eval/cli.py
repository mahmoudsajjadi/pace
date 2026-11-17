"""Command-line interface: ``mae-eval audit --log trace.jsonl``.

Trace format: JSON Lines, one generation or tool call per line. Fields:
  system            "mas" or "sas" (required)
  agent_id          string (default "agent")
  prompt_tokens, completion_tokens            integers (required unless "chunks" is given for streaming records)
  chunks            optional list of per-chunk token counts for a streamed completion (replaces completion_tokens)
  reasoning_tokens, scaffold_tokens           integers, default 0 (subsets of completion / prompt tokens)
  tool_calls        integer, default 0;  n_completions integer, default 1 (0 for a pure tool call)
  start, end        seconds on a common clock, default 0 (concurrent calls overlap)
Note: code/examples/sample_trace.jsonl is a hand-written synthetic example, not a trace of a model run.
A MAS/SAS ratio prints as n/a when both values are 0 (0/0 is undefined).
Exit status: 0 success, 1 input error, 2 parity violated (only with --assert-parity).
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, List, Optional, Sequence

from .auditor import ComputeParityError, EvaluationAuditor
from .tracker import ResourceTracker, Session
from .vector import DIMENSIONS, ResourceVector


class TraceError(ValueError):
    pass


def load_trace(path: str) -> Dict[str, List[dict]]:
    """Read a JSONL trace and group records by system. Raises TraceError with the line number on bad input."""
    groups: Dict[str, List[dict]] = {}
    with open(path, "r", encoding="utf-8") as fh:
        for no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise TraceError("line %d: invalid JSON (%s)" % (no, e.msg))
            if not isinstance(rec, dict):
                raise TraceError("line %d: expected a JSON object" % no)
            system = rec.get("system")
            if system not in ("mas", "sas"):
                raise TraceError("line %d: 'system' must be 'mas' or 'sas'" % no)
            if "chunks" not in rec and ("prompt_tokens" not in rec or "completion_tokens" not in rec):
                raise TraceError("line %d: need prompt_tokens and completion_tokens (or chunks)" % no)
            rec["_line"] = no
            groups.setdefault(system, []).append(rec)
    if not groups:
        raise TraceError("trace is empty")
    return groups


def session_from_records(records: List[dict], tracker: ResourceTracker) -> Session:
    with tracker.trace() as s:
        for r in records:
            try:
                common = dict(reasoning_tokens=int(r.get("reasoning_tokens", 0)), scaffold_tokens=int(r.get("scaffold_tokens", 0)),
                              tool_calls=int(r.get("tool_calls", 0)), start=float(r.get("start", 0.0)))
                agent = str(r.get("agent_id", "agent"))
                if "chunks" in r:
                    s.record_stream(agent, int(r.get("prompt_tokens", 0)), r["chunks"], **common)
                else:
                    s.record_call(agent, int(r["prompt_tokens"]), int(r["completion_tokens"]), n_completions=int(r.get("n_completions", 1)),
                                  end=float(r.get("end", common["start"])), **common)
            except (ValueError, TypeError) as e:
                raise TraceError("line %d: %s" % (r["_line"], e))
    return s


def _vec_dict(v: ResourceVector) -> dict:
    d = v.to_dict(include_scaffold=True)
    d["scaffold_pct"] = v.scaffold_pct
    return d


def run_audit(args: argparse.Namespace, out=None) -> int:
    out = out or sys.stdout
    try:
        groups = load_trace(args.log)
    except (OSError, TraceError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    tracker = ResourceTracker(args.model, "cli")
    priced = args.price_in is not None and args.price_out is not None
    if priced:
        tracker.register_pricing(args.price_in, args.price_out)
    vectors: Dict[str, ResourceVector] = {}
    try:
        for name, recs in groups.items():
            vectors[name] = session_from_records(recs, tracker).get_resource_vector(allow_missing_pricing=not priced)
    except (TraceError, ValueError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    report: dict = {"vectors": {k: _vec_dict(v) for k, v in vectors.items()}}
    status = 0
    if "mas" in vectors and "sas" in vectors:
        aud = EvaluationAuditor(vectors["mas"], vectors["sas"])
        dims = tuple(d.strip() for d in args.dims.split(",") if d.strip())
        report["ratios_mas_over_sas"] = aud.ratios()
        report["control_states"] = {k: v.value for k, v in aud.control_states(args.tolerance).items()}
        report["flags"] = [{"dimension": f.dimension, "ratio": f.ratio, "state": f.state.value, "message": f.message}
                           for f in aud.flag_confounders(args.tolerance)]
        try:
            aud.assert_compute_parity(args.tolerance, dims)
            report["parity"] = {"dims": list(dims), "tolerance": args.tolerance, "ok": True}
        except ComputeParityError as e:
            report["parity"] = {"dims": list(dims), "tolerance": args.tolerance, "ok": False, "detail": str(e)}
            if args.assert_parity:
                status = 2
    else:
        report["note"] = "only one system present; no comparison made"
    if args.json:
        json.dump(report, out, indent=2, default=lambda x: None if x != x else str(x))
        out.write("\n")
    else:
        for name, v in vectors.items():
            out.write("%s: " % name.upper() + ", ".join("%s=%s" % (d, getattr(v, d)) for d in DIMENSIONS))
            if v.scaffold_pct is not None:
                out.write(", scaffold=%.1f%%" % v.scaffold_pct)
            out.write("\n")
        if "ratios_mas_over_sas" in report:
            out.write("MAS/SAS ratios: " + ", ".join("%s=%s" % (k, "n/a" if r is None else "%.3g" % r) for k, r in report["ratios_mas_over_sas"].items()) + "\n")
            for f in report["flags"]:
                out.write("FLAG %s [%s]: %s\n" % (f["dimension"], f["state"], f["message"]))
            out.write("Parity on %s within %.3g: %s\n" % (",".join(report["parity"]["dims"]), args.tolerance, "OK" if report["parity"]["ok"] else "VIOLATED"))
    return status


def run_checklist(args: argparse.Namespace, out=None) -> int:
    out = out or sys.stdout
    if args.format == "latex":
        latex_str = r"""\begin{table}[h]
\centering
\small
\caption{\textbf{Compute-Matched Evaluation (CME) Reviewer Checklist Compliance.}}
\label{tab:cme_checklist}
\begin{tabular}{lp{8.5cm}c}
\toprule
Item & Evaluation Criterion & Response \\
\midrule
1. Resource Vector $\mathbf{R}$ & Full 6D vector reported ($R_{\text{reason}}, R_{\text{token}}, R_{\text{cost}}, R_{\text{lat}}, R_{\text{sample}}, R_{\text{sys}}$) & Yes \\
2. Equal Compute Baselines & Compared against CoT-SC or budget-matched tokens, not solely greedy & Yes \\
3. Scaffold Accounting & Prompts, roles, and echoed history deducted from reasoning budget & Yes \\
4. Dispersion and Sample Rigor & Benchmark test sizes ($N_{\text{items}}$) and paired statistics reported & Yes \\
5. Task Decomposability & Separated communicative debate from external tool/verifier access & Yes \\
6. Architecture Search & Disclosed cumulative search costs and negative configurations & Yes \\
\bottomrule
\end{tabular}
\end{table}
"""
        out.write(latex_str)
    elif args.format == "json":
        checklist_data = {
            "version": "1.0.0",
            "standard": "CME-Reviewer-Checklist",
            "items": [
                {"id": 1, "name": "Resource Vector R", "status": "Yes"},
                {"id": 2, "name": "Equal Compute Baseline", "status": "Yes"},
                {"id": 3, "name": "Scaffold Accounting", "status": "Yes"},
                {"id": 4, "name": "Dispersion and Sample Rigor", "status": "Yes"},
                {"id": 5, "name": "Task Decomposability and Tools", "status": "Yes"},
                {"id": 6, "name": "Architecture Search Disclosure", "status": "Yes"}
            ]
        }
        json.dump(checklist_data, out, indent=2)
        out.write("\n")
    else:  # markdown
        md_str = """# CME Reviewer Checklist
1. [x] **Resource Vector R:** Reported 6D vector (thinking, total, cost, latency, samples, sys).
2. [x] **Equal Compute Baseline:** Compared against CoT-SC or budget-matched tokens.
3. [x] **Scaffold Accounting:** Deducted prompt and history overhead from effective reasoning.
4. [x] **Dispersion and Sample Rigor:** Reported benchmark item counts and paired variance.
5. [x] **Task Decomposability:** Isolated communicative debate from external tool feedback.
6. [x] **Architecture Search:** Disclosed search compute and negative topologies.
"""
        out.write(md_str)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mae-eval", description="Compute-accounting audits for multi-agent LLM evaluations.")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("audit", help="audit a JSONL evaluation trace")
    a.add_argument("--log", required=True, help="path to a JSONL trace (see module docstring for the schema)")
    a.add_argument("--tolerance", type=float, default=0.05, help="relative tolerance for 'strictly controlled' (default 0.05)")
    a.add_argument("--dims", default="r_token", help="comma-separated dimensions that must match for parity (default r_token)")
    a.add_argument("--model", default="model", help="model name label for pricing")
    a.add_argument("--price-in", type=float, default=None, help="USD per million input tokens (you must supply it; none is bundled)")
    a.add_argument("--price-out", type=float, default=None, help="USD per million output tokens")
    a.add_argument("--assert-parity", action="store_true", help="exit with status 2 if parity is violated")
    a.add_argument("--json", action="store_true", help="print a JSON report")
    a.set_defaults(func=run_audit)

    c = sub.add_parser("checklist", help="generate a CME compliance checklist template (LaTeX, Markdown, or JSON)")
    c.add_argument("--format", choices=["markdown", "latex", "json"], default="markdown", help="output format (default: markdown)")
    c.set_defaults(func=run_checklist)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
