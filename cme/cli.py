"""cme command line: proxy | baseline | report."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, Sequence


def _proxy(a) -> int:
    from .proxy import serve
    srv = serve(a.upstream, a.log, a.port, a.host, a.price_in, a.price_out, a.api_key, a.item_file, a.system_label)
    print("cme proxy on http://%s:%d/v1 -> %s ; logging to %s (Ctrl+C to stop)" % (a.host, a.port, a.upstream, a.log), file=sys.stderr)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def _baseline(a) -> int:
    from .baseline import OpenAICompatClient, load_bench, ollama_digest, run_baseline
    items = load_bench(a.bench, a.max_items)
    digest = ollama_digest(a.model) if "11434" in a.base_url else None
    res = run_baseline(OpenAICompatClient(a.base_url, a.api_key), a.model, items, a.out, a.k, a.temperature, a.seed, a.max_tokens, digest,
                       progress=(lambda m: print(m, file=sys.stderr)) if a.verbose else None)
    print(json.dumps(res))
    return 0 if res["errors"] == 0 else 1


def _report(a) -> int:
    from .report import build_report, plot, to_latex
    try:
        rep = build_report(a.pool, a.logs, a.system, a.price_in, a.price_out, a.n_boot, a.perms, a.seed, a.k)
    except (OSError, ValueError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    g = rep["frontier_gap"]
    print("items %d | pool k=%d | system accuracy %.3f at %.0f tokens/item | frontier %.3f (%s) | gap %+.3f [%+.3f, %+.3f]" % (
        rep["n_items"], rep["pool_k"], g["system_accuracy"], g["system_mean_tokens"], g["frontier_at_system_tokens"], g["range_status"],
        g["gap"], g["ci_low"], g["ci_high"]))
    rc = rep["resource_card"]
    if rc:
        print("MAS/SAS ratios: " + ", ".join("%s=%s" % (k, "n/a" if v is None else "%.3g" % v) for k, v in rc["ratios_mas_over_sas"].items()))
    if a.json:
        json.dump(rep, open(a.json, "w", encoding="utf-8"), indent=2, default=str)
    if a.latex:
        open(a.latex, "w", encoding="utf-8").write(to_latex(rep))
    if a.plot:
        plot(rep, a.plot)
    if a.export_latex or a.export_markdown:
        from .rebuttal import row_from_report, to_latex as rb_tex, to_markdown
        rows = [row_from_report(rep, a.benchmark, a.model_label)]
        if a.export_latex:
            open(a.export_latex, "w", encoding="utf-8").write(rb_tex(rows))
        if a.export_markdown:
            open(a.export_markdown, "w", encoding="utf-8").write(to_markdown(rows))
    if a.export_rollout_card:
        from .rollout_card import write_block
        for path in write_block(rep, a.export_rollout_card, a.run_id):
            print("wrote " + path)
    return 0


def _classify(a) -> int:
    from mae_eval.classifier import classify_with_reason
    try:
        cfg = json.load(open(a.config, encoding="utf-8"))
        rung, rule, reason = classify_with_reason(cfg)
    except (OSError, ValueError, TypeError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    print(json.dumps({"rung": rung, "rule": rule, "reason": reason}))
    return 0


def _audit(a) -> int:
    from .audit import audit, render
    try:
        card = audit(a.input, a.baseline_config, a.tolerance, a.price_in, a.price_out)
    except (OSError, ValueError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    if a.json:
        print(json.dumps(card, indent=2, default=lambda x: None if x != x else str(x)))
    else:
        text = render(card)
        try:
            text.encode(sys.stdout.encoding or "utf-8")
        except (UnicodeEncodeError, LookupError):       # a console without box-drawing characters (for example a Windows code page): fall back to ASCII
            text = render(card, ascii_only=True)
        print(text)
    return 0 if card["ok"] or not a.strict else 2


def _dynamics(a) -> int:
    from .dynamics import analyse, excess_over_null, render
    try:
        res = analyse(a.log, a.n_boot, a.seed, a.first_round, a.last_round)
        if getattr(a, "null", None):
            null_res = analyse(a.null, a.n_boot, a.seed, a.first_round, a.last_round)
            res["excess_over_null"] = excess_over_null(res, null_res)
    except (OSError, ValueError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    if a.json:
        print(json.dumps(res, indent=2, default=str))
    else:
        print(render(res))
    return 0


def _hidden_profile(a) -> int:
    from .hidden_profile import generate, valid, validate
    try:
        items = generate(a.n, a.agents, a.criteria, a.split, a.margin, a.seed, a.format)
    except ValueError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    counts = validate(items)
    msg = "generated %d items (agents %d, criteria %d, split %d, margin %d, seed %d, format %s); decoy leads a view in violation: %d, target not leading pooled: %d, uncovered split criteria: %d" % (
        counts["items"], a.agents, a.criteria, a.split, a.margin, a.seed, a.format, counts["decoy_not_leading_a_view"], counts["target_not_leading_pooled"], counts["uncovered_split_criteria"])
    print(msg, file=sys.stderr)
    if not valid(counts):
        print("error: validity check failed; no output written", file=sys.stderr)
        return 1
    text = chr(10).join(json.dumps(it) for it in items) + chr(10)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    return 0


def _frontier(a) -> int:
    from .report import frontier_report, plot_frontier, system_points
    try:
        fr = frontier_report(a.samples, a.k, a.perms, a.seed)
        pts = system_points(a.logs) if a.logs else []
    except (OSError, ValueError, KeyError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    print("items %d | pool k=%d | greedy accuracy %s" % (fr["n_items"], fr["pool_k"], "n/a" if fr["greedy_accuracy"] is None else "%.3f" % fr["greedy_accuracy"]))
    print("k  mean tokens  SC accuracy  isotonic")
    for i, (t, x, y) in enumerate(zip(fr["tokens"], fr["sc_accuracy"], fr["isotonic"]), 1):
        print("%-2d %11.0f  %11.3f  %8.3f" % (i, t, x, y))
    for p in pts:
        print("system %-12s accuracy %.3f at %.0f tokens/item (n=%d)" % (p["system"], p["accuracy"], p["mean_tokens"], p["n_items"]))
    if a.json:
        json.dump({"frontier": fr, "systems": pts}, open(a.json, "w", encoding="utf-8"), indent=2)
    if a.out:
        plot_frontier(fr, pts, a.out)
    return 0


def _rebuttal(a) -> int:
    from .rebuttal import rows_from_contrasts, to_latex as rb_tex, to_markdown
    try:
        rows = rows_from_contrasts(a.contrasts, a.study)
    except (OSError, KeyError, ValueError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    if not rows:
        print("error: no rows", file=sys.stderr)
        return 1
    if a.export_latex:
        open(a.export_latex, "w", encoding="utf-8").write(rb_tex(rows))
    if a.export_markdown:
        open(a.export_markdown, "w", encoding="utf-8").write(to_markdown(rows))
    if not (a.export_latex or a.export_markdown):
        print(to_markdown(rows))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cme", description="Compute-matched evaluation: measure systems against the self-consistency frontier.")
    sub = p.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("proxy", help="OpenAI-compatible logging proxy")
    x.add_argument("--upstream", default="http://localhost:11434/v1")
    x.add_argument("--port", type=int, default=8089)
    x.add_argument("--host", default="127.0.0.1")
    x.add_argument("--log", default="run.jsonl")
    x.add_argument("--price-in", type=float, default=None, help="USD per million input tokens (never bundled)")
    x.add_argument("--price-out", type=float, default=None)
    x.add_argument("--api-key", default=None)
    x.add_argument("--system-label", default="mas", help="value of the log's system field when a request has no X-CME-System header")
    x.add_argument("--item-file", default=None, help="file whose first line is the current item id, used when a request has no X-CME-Item header (serial runs of third-party code)")
    x.set_defaults(func=_proxy)
    b = sub.add_parser("baseline", help="greedy + k-sample pool, cached and resumable")
    b.add_argument("--model", required=True)
    b.add_argument("--bench", required=True, help="path to JSONL {id, question, answer}, or 'toy' (synthetic smoke test)")
    b.add_argument("--base-url", default="http://localhost:11434/v1")
    b.add_argument("--api-key", default="none")
    b.add_argument("--k", type=int, default=16)
    b.add_argument("--temperature", type=float, default=0.7)
    b.add_argument("--seed", type=int, default=0)
    b.add_argument("--max-tokens", type=int, default=2048)
    b.add_argument("--max-items", type=int, default=None)
    b.add_argument("--out", default="baseline_cache.jsonl")
    b.add_argument("--verbose", action="store_true")
    b.set_defaults(func=_baseline)
    r = sub.add_parser("report", help="frontier gap, resource card, LaTeX table and figure")
    r.add_argument("--pool", required=True, help="baseline cache from `cme baseline`")
    r.add_argument("--logs", required=True, help="system log (calls and results)")
    r.add_argument("--system", default="mas")
    r.add_argument("--price-in", type=float, default=None)
    r.add_argument("--price-out", type=float, default=None)
    r.add_argument("--k", type=int, default=None, help="use the first k samples per item")
    r.add_argument("--n-boot", type=int, default=2000)
    r.add_argument("--perms", type=int, default=100)
    r.add_argument("--seed", type=int, default=0)
    r.add_argument("--json", default=None)
    r.add_argument("--latex", default=None)
    r.add_argument("--plot", default=None, help="vector figure path (.pdf)")
    r.add_argument("--export-latex", default=None, help="write the nine-column rebuttal table for this run (LaTeX)")
    r.add_argument("--export-markdown", default=None, help="write the nine-column rebuttal table for this run (Markdown)")
    r.add_argument("--benchmark", default="n/a", help="benchmark label for the exported row")
    r.add_argument("--model-label", default="n/a", help="model label for the exported row")
    r.add_argument("--export-rollout-card", default=None, metavar="PREFIX", help="write PREFIX.json, PREFIX.yaml and PREFIX.tex: a CME compute block for a rollout card (arXiv:2605.12131)")
    r.add_argument("--run-id", default="run", help="target id used in the rollout-card annotation rows")
    r.set_defaults(func=_report)
    c = sub.add_parser("classify", help="baseline rung (A to D) of a single-agent configuration given as JSON")
    c.add_argument("--config", required=True, help="JSON file; keys are listed in code/mae_eval/classifier.py")
    c.set_defaults(func=_classify)
    u = sub.add_parser("audit", help="one-screen diagnostic card for a run log (mas and sas calls) or a baseline configuration (JSON)")
    u.add_argument("input", help="JSONL run log with 'mas' and 'sas' calls, or a JSON baseline configuration")
    u.add_argument("--baseline-config", default=None, help="JSON configuration of the single-agent baseline, to classify its rung when INPUT is a log")
    u.add_argument("--tolerance", type=float, default=0.05)
    u.add_argument("--price-in", type=float, default=None)
    u.add_argument("--price-out", type=float, default=None)
    u.add_argument("--json", action="store_true")
    u.add_argument("--strict", action="store_true", help="exit with status 2 when the badge is a warning")
    u.set_defaults(func=_audit)
    d = sub.add_parser("dynamics", help="flip counts, tau rates, implied threshold, peer correlation, K_eff and tokens by round from a debate log")
    d.add_argument("log", help="JSONL with item, agent, round, correct (and optionally prompt_tokens, completion_tokens) per agent answer")
    d.add_argument("--null", default=None, help="optional no-communication control JSONL log to compute excess transition rates and excess peer correlation")
    d.add_argument("--n-boot", type=int, default=1000)
    d.add_argument("--seed", type=int, default=0)
    d.add_argument("--first-round", type=int, default=None)
    d.add_argument("--last-round", type=int, default=None)
    d.add_argument("--json", action="store_true")
    d.set_defaults(func=_dynamics)
    h = sub.add_parser("hidden-profile", help="generate synthetic split-evidence (hidden-profile) items and check their validity")
    h.add_argument("--n", type=int, default=100, help="number of items")
    h.add_argument("--agents", type=int, default=5)
    h.add_argument("--criteria", type=int, default=10, help="total number of criteria")
    h.add_argument("--split", type=int, default=6, help="number of criteria divided among the agents (the rest are shared)")
    h.add_argument("--margin", type=int, default=3, help="score gap per criterion between the favoured and the disfavoured candidate (at least 2)")
    h.add_argument("--seed", type=int, default=42)
    h.add_argument("--format", choices=["text", "numeric"], default="text")
    h.add_argument("--out", default=None, help="output JSONL (default: standard output)")
    h.set_defaults(func=_hidden_profile)
    f = sub.add_parser("frontier", help="self-consistency frontier of a sample pool, optionally with system points from a run log")
    f.add_argument("--samples", required=True, help="baseline cache from `cme baseline` (greedy + sampled completions per item)")
    f.add_argument("--logs", default=None, help="run log; every value of its 'system' field is drawn as a point")
    f.add_argument("--k", type=int, default=None)
    f.add_argument("--perms", type=int, default=100)
    f.add_argument("--seed", type=int, default=0)
    f.add_argument("--json", default=None)
    f.add_argument("--out", default=None, help="figure path (.pdf vector, or .png)")
    f.set_defaults(func=_frontier)
    t = sub.add_parser("rebuttal", help="nine-column rebuttal table from a contrasts CSV (default: outputs/baseline_tier_contrasts.csv)")
    t.add_argument("--contrasts", "--data", dest="contrasts", default="outputs/baseline_tier_contrasts.csv",
                   help="contrasts CSV with columns study, category (rung), baseline, key 'Study|bench|model|arm', p_base, p_mas")
    t.add_argument("--study", default=None)
    t.add_argument("--export-latex", default=None)
    t.add_argument("--export-markdown", default=None)
    t.set_defaults(func=_rebuttal)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    a = build_parser().parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
