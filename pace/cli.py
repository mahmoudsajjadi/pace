"""pace command line: proxy | baseline | report."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence


def _proxy(a) -> int:
    from .proxy import serve

    srv = serve(
        a.upstream,
        a.log,
        a.port,
        a.host,
        a.price_in,
        a.price_out,
        a.api_key,
        a.item_file,
        a.system_label,
    )
    print(
        "pace proxy on http://%s:%d/v1 -> %s ; logging to %s (Ctrl+C to stop)"
        % (a.host, a.port, a.upstream, a.log),
        file=sys.stderr,
    )
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def _baseline(a) -> int:
    from .baseline import OpenAICompatClient, load_bench, ollama_digest, run_baseline

    items = load_bench(a.bench, a.max_items)
    digest = ollama_digest(a.model) if "11434" in a.base_url else None
    res = run_baseline(
        OpenAICompatClient(a.base_url, a.api_key),
        a.model,
        items,
        a.out,
        a.k,
        a.temperature,
        a.seed,
        a.max_tokens,
        digest,
        progress=(lambda m: print(m, file=sys.stderr)) if a.verbose else None,
    )
    print(json.dumps(res))
    return 0 if res["errors"] == 0 else 1


def _report(a) -> int:
    from .report import build_report, plot, to_latex

    try:
        rep = build_report(
            a.pool,
            a.logs,
            a.system,
            a.price_in,
            a.price_out,
            a.n_boot,
            a.perms,
            a.seed,
            a.k,
        )
    except (OSError, ValueError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    g = rep["frontier_gap"]
    print(
        "items %d | pool k=%d | system accuracy %.3f at %.0f tokens/item | frontier %.3f (%s) | gap %+.3f [%+.3f, %+.3f]"
        % (
            rep["n_items"],
            rep["pool_k"],
            g["system_accuracy"],
            g["system_mean_tokens"],
            g["frontier_at_system_tokens"],
            g["range_status"],
            g["gap"],
            g["ci_low"],
            g["ci_high"],
        )
    )
    rc = rep["resource_card"]
    if rc:
        print(
            "MAS/SAS ratios: "
            + ", ".join(
                "%s=%s" % (k, "n/a" if v is None else "%.3g" % v)
                for k, v in rc["ratios_mas_over_sas"].items()
            )
        )
    if a.json:
        json.dump(rep, open(a.json, "w", encoding="utf-8"), indent=2, default=str)
    if a.latex:
        open(a.latex, "w", encoding="utf-8").write(to_latex(rep))
    if a.plot:
        plot(rep, a.plot)
    if a.export_latex or a.export_markdown:
        from .rebuttal import row_from_report, to_markdown
        from .rebuttal import to_latex as rb_tex

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


def _inflate(a) -> int:
    from .inflate import estimate_wrong_options, inflate_report, successes_from_rows

    try:
        rows = [json.loads(line) for line in open(a.samples, encoding="utf-8") if line.strip()]
        succ, n = successes_from_rows(rows)
        ks = [int(x) for x in a.k.split(",") if x.strip()]
        w = None
        if a.wrong_options == "auto":
            w = estimate_wrong_options(rows)
            if w is None:
                raise ValueError("--wrong-options auto needs rows with an answer label and at least one item with two wrong samples")
        elif a.wrong_options:
            w = float(a.wrong_options)
        rep = inflate_report(succ, n, ks, wrong_options=w)
    except (OSError, ValueError, KeyError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    if a.json:
        print(json.dumps(rep, indent=1))
        return 0
    print("items=%d pool=%d  Beta(alpha=%.3f, beta=%.3f)  single-sample accuracy %.3f (observed %.3f)" % (rep["n_items"], rep["pool_size"], rep["alpha"], rep["beta"], rep["mean_single_sample_accuracy"], rep["single_sample_accuracy_observed"]))
    print("%5s %10s %13s %14s %18s" % ("K", "predicted", "pool_observed", "over_1_sample", "plurality(W=%s)" % (("%.2f" % rep["wrong_options"]) if rep.get("wrong_options") else "-")))
    for r in rep["inflation"]:
        print("%5d %10.3f %13s %14.3f %18s" % (r["K"], r["predicted"], ("%.3f" % r["pool_observed"]) if "pool_observed" in r else "n/a", r["over_single_sample"], ("%.3f" % r["predicted_plurality"]) if "predicted_plurality" in r else "n/a"))
    print(rep["model"])
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
        except (
            UnicodeEncodeError,
            LookupError,
        ):  # a console without box-drawing characters (for example a Windows code page): fall back to ASCII
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


def _import_logs(a) -> int:
    from .importers import load_and_import, write_jsonl

    try:
        count = write_jsonl(load_and_import(a.input, a.format), a.output)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    print("wrote %d PACE records to %s" % (count, a.output))
    return 0


def _card(a) -> int:
    from .card import build_card, build_card_v2, load_log, to_latex, to_latex_card_v1, to_latex_v2, to_markdown

    fmt = a.format or ("json" if a.json else ("latex" if a.latex else None))
    try:
        if a.v2:
            rows = load_log(a.log)
            if fmt == "latex" and a.format == "latex":          # --v2 --format latex: the PACE Card v1.0 table, as in Studio and the Workbench
                text = to_latex_card_v1(build_card(rows))
            elif fmt == "latex":                                  # --v2 --latex keeps the compact five-row snippet of the v2 card
                text = to_latex_v2(build_card_v2(rows, log_path=a.log))
            elif fmt == "markdown":
                text = to_markdown(build_card(rows))
            else:
                text = json.dumps(build_card_v2(rows, log_path=a.log), indent=2)
        else:
            card = build_card(load_log(a.log))
            text = json.dumps(card, indent=2) if fmt == "json" else (to_latex(card) if fmt == "latex" else to_markdown(card))
        if a.output:
            open(a.output, "w", encoding="utf-8").write(text)
        else:
            print(text, end="")
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


def _validate_log(a) -> int:
    from .validate import render_text, validate

    rep = validate(a.log)
    code = rep["exit_code"]
    if code == 0 and a.strict and rep["n_warnings"]:
        code = 1
    rep["exit_code"] = code
    if a.report:
        with open(a.report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(rep, fh, indent=2)
            fh.write("\n")
    if a.json:
        print(json.dumps(rep, indent=2))
    else:
        print(render_text(rep), end="")
    return code


def _doctor(a) -> int:
    from .doctor import collect, render_text

    rep = collect()
    print(json.dumps(rep, indent=2) if a.json else render_text(rep), end="\n" if a.json else "")
    return 0 if rep["ok"] else 1


def _compare(a) -> int:
    """Exit codes: 0 verdict printed (also RULES OUT unless --fail-on-ruled-out), 1 RULES OUT with --fail-on-ruled-out, 2 a trace could not be read."""
    from .card import load_log
    from .compare import compare_traces, to_latex, to_markdown

    try:
        rep = compare_traces(load_log(a.baseline), load_log(a.candidate), tol=a.tol, margin=a.margin, min_items=a.min_items)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    text = json.dumps(rep, indent=2) + "\n" if a.format == "json" else (to_latex(rep) if a.format == "latex" else to_markdown(rep))
    if a.output:
        with open(a.output, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    else:
        print(text, end="")
    if a.fail_on_ruled_out and rep["verdict"]["label"] == "RULES OUT":
        print("PACE gate: candidate RULES OUT (%s)" % rep["verdict"]["reason"], file=sys.stderr)
        return 1
    return 0


def _studio(a) -> int:
    import webbrowser
    from pathlib import Path

    target = Path(__file__).with_name("studio.html").resolve().as_uri()
    webbrowser.open(target)
    print("opened PACE Studio: %s" % target)
    return 0


def _workbench(a) -> int:
    from .workbench import export_html, serve

    if a.export_html:
        export_html(a.export_html)
        print("wrote " + a.export_html)
    if a.serve:
        srv = serve(a.host, a.port, a.no_browser)
        print("PACE Workbench: http://%s:%d/" % (a.host, a.port), file=sys.stderr)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


def _card_v7(a) -> int:
    from .workbench import card_from_file, card_v7_to_latex, card_v7_to_markdown

    try:
        card = card_from_file(a.log, a.baseline_log)
        if a.json:
            text = json.dumps(card, indent=2)
        elif a.latex:
            text = card_v7_to_latex(card)
        else:
            text = card_v7_to_markdown(card)
        if a.output:
            open(a.output, "w", encoding="utf-8").write(text)
        else:
            print(text, end="")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    return 0


def _pool_size(a) -> int:
    from .pool_sizer import compute_k_tok

    result = compute_k_tok(
        a.agents, a.rounds, a.prompt_tokens, a.msg_tokens, a.topology
    )
    result.pop("b_eff", None)
    if a.json:
        print(json.dumps(result, indent=2))
    else:
        print(
            "k_tok %.3f (r=%.4f), recommended pool size %d"
            % (result["k_tok"], result["r"], result["recommended_pool_size"])
        )
    return 0


def _simulate(a) -> int:
    from . import simulator

    if a.mode == "voting":
        result = simulator.simulate_correlated_voting(
            a.items, a.agents, a.p_mean, a.rho, a.choices, a.seed
        )
    elif a.mode == "debate":
        result = simulator.simulate_debate_dynamics(
            a.items,
            a.agents,
            a.rounds,
            a.p_mean,
            a.regime,
            {"a": a.rate_a, "b": a.rate_b},
            a.replicates,
            a.verifier_fp,
            a.verifier_fn,
            a.seed,
        )
    else:
        result = simulator.simulate_scaffolding_scaling_curve(
            a.budgets, a.agents, a.rounds, a.prompt_tokens, a.msg_tokens
        )
    if a.out:
        with open(a.out, "w", encoding="utf-8") as handle:
            if isinstance(result, list):
                handle.writelines(json.dumps(row) + "\n" for row in result)
            else:
                handle.write(json.dumps(result) + "\n")
    else:
        print(json.dumps(result, indent=2))
    return 0


def _meta(a) -> int:
    import csv

    from .meta_engine import (
        build_che_covariance,
        compute_effect_sizes,
        der_simonian_laird_pool,
    )

    if a.contrasts == "outputs/baseline_tier_contrasts.csv" and not os.path.exists(a.contrasts) and os.path.exists("data/baseline_tier_contrasts.csv"):
        a.contrasts = "data/baseline_tier_contrasts.csv"   # release tree layout: the corpus lives in data/
    with open(a.contrasts, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if a.reml:
        # the paper's pooled model: three-level REML on log odds ratios with CR2 intervals (default selection: Category B/C, the B9 model, beta = -0.195)
        try:
            from .reml import reml_pool
        except ImportError as e:  # numpy, pandas and scipy are needed
            print("error: pace meta --reml needs numpy, pandas and scipy (%s)" % e, file=sys.stderr)
            return 1
        keep = set((a.category or "BC").upper().replace("BC", "B,C").split(","))
        sel = [{"study": r.get("study", "study"), "p_mas": float(r["p_mas"]), "p_base": float(r["p_base"]), "n": float(r.get("n", 1))} for r in rows if r.get("category", "") in keep]
        if not sel:
            print("error: no contrasts with category %s (the file needs a category column)" % "".join(sorted(keep)), file=sys.stderr)
            return 1
        out = reml_pool(sel, a.phi)
        out["selection"] = "category " + "/".join(sorted(keep))
        print(json.dumps(out, indent=2) if a.json else json.dumps(out))
        return 0
    if a.category:
        keep = set(a.category.upper().replace("BC", "B,C").split(","))
        rows = [r for r in rows if r.get("category", "") in keep]
        if not rows:
            print("error: no contrasts with category %s (the file needs a category column)" % a.category, file=sys.stderr)
            return 1
    effects = [
        compute_effect_sizes(
            float(row["p_mas"]), float(row["p_base"]), int(float(row.get("n", 1))), a.phi
        )
        for row in rows
    ]
    np_mod = __import__("numpy")
    y = np_mod.array(
        [
            effect[a.scale] if a.scale != "delta" else effect["delta"]
            for effect in effects
        ]
    )
    if a.scale == "cohen_h":
        v = np_mod.array([effect["v_cohen_h"] for effect in effects])
    elif a.scale == "delta":
        v_list = []
        for row in rows:
            pm = float(row["p_mas"])
            pb = float(row["p_base"])
            n_val = max(1.0, float(row.get("n", 1)))
            am, ab = pm * (1.0 - pm), pb * (1.0 - pb)
            v_d = max(1e-10, (am + ab - 2.0 * a.phi * (am * ab) ** 0.5) / n_val)
            v_list.append(v_d)
        v = np_mod.array(v_list)
    else:
        v = np_mod.array([effect["v_log_or"] for effect in effects])
    result = {
        "estimator": "DerSimonian-Laird",
        "note": "DerSimonian-Laird random-effects pooling of the selected contrasts; it is NOT the three-level REML with CR2 intervals reported in the paper (see analysis/run_k9_reml.py). Select contrasts with --category (A, B, C, BC). The correlated-error covariance matrix is only printed with --covariance.",
        "scale": a.scale,
        "n_contrasts": len(rows),
        "effects": effects,
    }
    if a.covariance:
        result["covariance"] = build_che_covariance(rows, a.rho_block).tolist()
    if len(rows) > 1:
        result["pooled"] = der_simonian_laird_pool(
            y, v, [row.get("study", "study") for row in rows]
        )
    print(json.dumps(result, indent=2) if a.json else json.dumps(result))
    return 0


def _power(a) -> int:
    from .meta_engine import prospective_power_analysis

    if a.ledger:
        from .power_audit import audit_ledger, read_ledger

        result = audit_ledger(read_ledger(a.ledger), tuple(a.phis))
        print(json.dumps(result, indent=2) if a.json else json.dumps(result))
        return 0
    if a.p_base is None or a.delta is None:
        print("error: --p-base and --delta are required unless --ledger is given", file=sys.stderr)
        return 1

    result = prospective_power_analysis(
        a.p_base, a.delta, a.n_items, a.power, a.alpha, a.phi, a.shared_arms
    )
    print(json.dumps(result, indent=2) if a.json else json.dumps(result))
    return 0


def _benchmark_gen(a) -> int:
    from .escape_benchmarks import (
        evaluate_with_verifier_threshold,
        generate_clue_grid_items,
        generate_distributed_code_items,
    )

    if a.route == "clue_grid":
        result = generate_clue_grid_items(a.items, a.agents, a.seed)
    elif a.route == "distributed_code":
        result = generate_distributed_code_items(a.items, a.agents, a.seed)
    else:
        result = [
            evaluate_with_verifier_threshold(0.5, 0.2, 0.1, epsilon, 0.1)
            for epsilon in a.epsilons
        ]
    with open(a.out, "w", encoding="utf-8") as handle:
        handle.writelines(json.dumps(row) + "\n" for row in result)
    return 0


def _aggregate_open(a) -> int:
    from .open_ended import mbr_centroid_select

    records = [
        json.loads(line) for line in open(a.input, encoding="utf-8") if line.strip()
    ]
    output = []
    for row in records:
        candidates = row.get("candidates", row.get("answers", []))
        output.append(
            {
                "item": row.get("item", row.get("id", len(output))),
                **mbr_centroid_select(candidates, a.metric, row.get("token_costs")),
            }
        )
    text = "".join(json.dumps(row) + "\n" for row in output)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
    else:
        print(text, end="")
    return 0


def _waterfall_values(a) -> tuple[float, float, float]:
    """(greedy, sampled/frontier, system) accuracies for the waterfall: explicit --p-greedy/--p-sampled/--p-mas, or read from a `pace report --json` file
    (greedy_accuracy, frontier at the system's tokens, system accuracy) or a `pace card --json` file with a single-trace block (round-1 single, round-1 vote,
    final vote). Nothing is assumed: missing values are an error."""
    if a.p_greedy is not None and a.p_sampled is not None and a.p_mas is not None:
        return a.p_greedy, a.p_sampled, a.p_mas
    if not a.input:
        raise ValueError("waterfall needs --input (a pace report or card JSON) or all of --p-greedy, --p-sampled and --p-mas")
    payload = json.load(open(a.input, encoding="utf-8"))
    if "frontier_gap" in payload:
        g = payload["frontier_gap"]
        if payload.get("greedy_accuracy") is None:
            raise ValueError("the report has no greedy accuracy (the pool has no greedy run)")
        return float(payload["greedy_accuracy"]), float(g["frontier_at_system_tokens"]), float(g["system_accuracy"])
    if "single_trace" in payload:
        t = payload["single_trace"]
        return float(t["p_round1_single"]), float(t["p_round1_vote"]), float(t["p_final_vote"])
    raise ValueError("%s is neither a pace report JSON (frontier_gap) nor a pace card JSON with single_trace" % a.input)


def _plot(a) -> int:
    from . import plotting

    if a.kind == "waterfall":
        try:
            p_g, p_s, p_m = _waterfall_values(a)
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
            print("error: %s" % e, file=sys.stderr)
            return 1
        result = plotting.svg_waterfall_decomposition(p_g, p_s, p_m)
    elif a.kind == "phase":
        result = plotting.svg_phase_diagram()
    elif a.kind == "frontier":
        result = plotting.svg_frontier_curve(json.load(open(a.input, encoding="utf-8")))
    else:
        payload = json.load(open(a.input, encoding="utf-8"))
        result = plotting.svg_influence_curves(
            payload["by_correct_peers"],
            payload.get("fit_result", payload),
            payload.get("k_agents", 3),
        )
    open(a.out, "w", encoding="utf-8").write(result)
    return 0


def _hidden_profile(a) -> int:
    from .hidden_profile import generate, valid, validate

    try:
        items = generate(a.n, a.agents, a.criteria, a.split, a.margin, a.seed, a.format)
    except ValueError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    counts = validate(items)
    msg = (
        "generated %d items (agents %d, criteria %d, split %d, margin %d, seed %d, format %s); decoy leads a view in violation: %d, target not leading pooled: %d, uncovered split criteria: %d"
        % (
            counts["items"],
            a.agents,
            a.criteria,
            a.split,
            a.margin,
            a.seed,
            a.format,
            counts["decoy_not_leading_a_view"],
            counts["target_not_leading_pooled"],
            counts["uncovered_split_criteria"],
        )
    )
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
    import numpy as np

    from .baseline import load_pool
    from .frontier import (
        crossfit_frontier,
        envelope_increasing,
        frontier_at,
        frontier_curve,
        frontier_gap,
    )
    from .report import frontier_report, plot_frontier, read_run, system_points

    estimator = getattr(a, "estimator", "isotonic")
    claim_direction = getattr(a, "claim_direction", "auto")
    n_splits = getattr(a, "n_splits", 200)

    try:
        fr = frontier_report(a.samples, a.k, a.perms, a.seed)
        pts = system_points(a.logs) if a.logs else []
        if estimator != "isotonic":
            pool, _, _ = load_pool(a.samples, a.k)
            ids, acc, tok = pool.curves(a.perms, a.seed)
            fr["estimator"] = estimator
            if estimator in ("envelope", "directional"):
                fr["envelope"] = envelope_increasing(
                    np.asarray(fr["sc_accuracy"], dtype=float)
                ).tolist()
            if estimator in ("crossfit", "directional"):
                fr["crossfit"] = [
                    crossfit_frontier(acc, tok, float(t), n_splits=n_splits, seed=a.seed)[0]
                    for t in fr["tokens"]
                ]
            tk_all, ak_all = frontier_curve(acc, tok)
            pos = {i: idx for idx, i in enumerate(ids)}
            for p in pts:
                calls, results, _ = read_run(a.logs, p["system"])
                common = [i for i in ids if i in results and i in calls]
                if len(common) >= 2:
                    sel = [pos[i] for i in common]
                    sc = np.array([float(results[i]) for i in common])
                    st = np.array(
                        [
                            float(
                                sum(
                                    c["prompt_tokens"] + c["completion_tokens"]
                                    for c in calls[i]
                                )
                            )
                            for i in common
                        ]
                    )
                    fg = frontier_gap(
                        acc[sel],
                        tok[sel],
                        sc,
                        st,
                        seed=a.seed,
                        estimator=estimator,
                        claim_direction=claim_direction,
                        n_splits=n_splits,
                    )
                    for k_fg in (
                        "frontier_at_system_tokens",
                        "gap",
                        "ci_low",
                        "ci_high",
                        "p_gap_le_0",
                        "p_two_sided",
                        "range_status",
                        "estimator",
                        "claim_direction",
                        "selected_estimator",
                        "frontier_crossfit",
                        "gap_crossfit",
                        "crossfit_ci_low",
                        "crossfit_ci_high",
                        "crossfit_p_gap_le_0",
                        "crossfit_p_two_sided",
                        "frontier_envelope",
                        "gap_envelope",
                        "envelope_ci_low",
                        "envelope_ci_high",
                        "envelope_p_gap_le_0",
                        "envelope_p_two_sided",
                        "frontier_isotonic",
                        "gap_isotonic",
                    ):
                        if k_fg in fg:
                            p[k_fg] = fg[k_fg]
                else:
                    t_sys = float(p["mean_tokens"])
                    if estimator == "envelope":
                        f_val, status = frontier_at(tk_all, ak_all, t_sys, estimator="envelope")
                        p["frontier_at_system_tokens"] = f_val
                        p["gap"] = float(p["accuracy"] - f_val)
                        p["range_status"] = status
                    elif estimator == "crossfit":
                        f_val, status = crossfit_frontier(acc, tok, t_sys, n_splits=n_splits, seed=a.seed)
                        p["frontier_at_system_tokens"] = f_val
                        p["gap"] = float(p["accuracy"] - f_val)
                        p["range_status"] = status
                    else:
                        f_cf, status_cf = crossfit_frontier(acc, tok, t_sys, n_splits=n_splits, seed=a.seed)
                        f_env, status_env = frontier_at(tk_all, ak_all, t_sys, estimator="envelope")
                        f_iso, _ = frontier_at(tk_all, ak_all, t_sys, estimator="isotonic")
                        sel_est = (
                            "envelope"
                            if (claim_direction == "positive" or (claim_direction == "auto" and p["accuracy"] > f_iso))
                            else "crossfit"
                        )
                        p["estimator"] = "directional"
                        p["claim_direction"] = claim_direction
                        p["selected_estimator"] = sel_est
                        p["frontier_crossfit"] = f_cf
                        p["gap_crossfit"] = float(p["accuracy"] - f_cf)
                        p["frontier_envelope"] = f_env
                        p["gap_envelope"] = float(p["accuracy"] - f_env)
                        p["frontier_isotonic"] = f_iso
                        p["gap_isotonic"] = float(p["accuracy"] - f_iso)
                        p["frontier_at_system_tokens"] = f_env if sel_est == "envelope" else f_cf
                        p["gap"] = float(p["accuracy"] - p["frontier_at_system_tokens"])
                        p["range_status"] = status_env if sel_est == "envelope" else status_cf
    except (OSError, ValueError, KeyError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    print(
        "items %d | pool k=%d | greedy accuracy %s"
        % (
            fr["n_items"],
            fr["pool_k"],
            "n/a" if fr["greedy_accuracy"] is None else "%.3f" % fr["greedy_accuracy"],
        )
    )
    if estimator == "isotonic":
        print("k  mean tokens  SC accuracy  isotonic")
        for i, (t, x, y) in enumerate(
            zip(fr["tokens"], fr["sc_accuracy"], fr["isotonic"]), 1
        ):
            print("%-2d %11.0f  %11.3f  %8.3f" % (i, t, x, y))
    elif estimator == "envelope":
        print("k  mean tokens  SC accuracy  isotonic  envelope")
        for i, (t, x, y, ev) in enumerate(
            zip(fr["tokens"], fr["sc_accuracy"], fr["isotonic"], fr["envelope"]), 1
        ):
            print("%-2d %11.0f  %11.3f  %8.3f  %8.3f" % (i, t, x, y, ev))
    elif estimator == "crossfit":
        print("k  mean tokens  SC accuracy  isotonic  crossfit")
        for i, (t, x, y, cf) in enumerate(
            zip(fr["tokens"], fr["sc_accuracy"], fr["isotonic"], fr["crossfit"]), 1
        ):
            print("%-2d %11.0f  %11.3f  %8.3f  %8.3f" % (i, t, x, y, cf))
    else:
        print("k  mean tokens  SC accuracy  isotonic  crossfit  envelope")
        for i, (t, x, y, cf, ev) in enumerate(
            zip(
                fr["tokens"],
                fr["sc_accuracy"],
                fr["isotonic"],
                fr["crossfit"],
                fr["envelope"],
            ),
            1,
        ):
            print("%-2d %11.0f  %11.3f  %8.3f  %8.3f  %8.3f" % (i, t, x, y, cf, ev))
    for p in pts:
        if estimator == "directional":
            print(
                "system %-12s accuracy %.3f at %.0f tokens/item (n=%d) | crossfit %.3f (gap %+.3f) | envelope %.3f (gap %+.3f) | selected %s"
                % (
                    p["system"],
                    p["accuracy"],
                    p["mean_tokens"],
                    p["n_items"],
                    p["frontier_crossfit"],
                    p["gap_crossfit"],
                    p["frontier_envelope"],
                    p["gap_envelope"],
                    p["selected_estimator"],
                )
            )
        elif estimator != "isotonic" and "frontier_at_system_tokens" in p:
            print(
                "system %-12s accuracy %.3f at %.0f tokens/item (n=%d) | %s %.3f (gap %+.3f)"
                % (
                    p["system"],
                    p["accuracy"],
                    p["mean_tokens"],
                    p["n_items"],
                    estimator,
                    p["frontier_at_system_tokens"],
                    p["gap"],
                )
            )
        else:
            print(
                "system %-12s accuracy %.3f at %.0f tokens/item (n=%d)"
                % (p["system"], p["accuracy"], p["mean_tokens"], p["n_items"])
            )
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"frontier": fr, "systems": pts}, fh, indent=2)
    if a.out:
        plot_frontier(fr, pts, a.out)
    return 0


def _rebuttal(a) -> int:
    from .rebuttal import rows_from_contrasts, to_markdown
    from .rebuttal import to_latex as rb_tex

    if a.contrasts == "outputs/baseline_tier_contrasts.csv" and not os.path.exists(a.contrasts) and os.path.exists("data/baseline_tier_contrasts.csv"):
        a.contrasts = "data/baseline_tier_contrasts.csv"   # release tree layout: the corpus lives in data/
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
    p = argparse.ArgumentParser(
        prog="pace",
        description="Compute-matched evaluation: measure systems against the self-consistency frontier.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("proxy", help="OpenAI-compatible logging proxy")
    x.add_argument("--upstream", default="http://localhost:11434/v1")
    x.add_argument("--port", type=int, default=8089)
    x.add_argument("--host", default="127.0.0.1")
    x.add_argument("--log", default="run.jsonl")
    x.add_argument(
        "--price-in",
        type=float,
        default=None,
        help="USD per million input tokens (never bundled)",
    )
    x.add_argument("--price-out", type=float, default=None)
    x.add_argument("--api-key", default=None)
    x.add_argument(
        "--system-label",
        default="mas",
        help="value of the log's system field when a request has no X-PACE-System header",
    )
    x.add_argument(
        "--item-file",
        default=None,
        help="file whose first line is the current item id, used when a request has no X-PACE-Item header (serial runs of third-party code)",
    )
    x.set_defaults(func=_proxy)
    b = sub.add_parser("baseline", help="greedy + k-sample pool, cached and resumable")
    b.add_argument("--model", required=True)
    b.add_argument(
        "--bench",
        required=True,
        help="path to JSONL {id, question, answer}, or 'toy' (synthetic smoke test)",
    )
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
    r = sub.add_parser(
        "report", help="frontier gap, resource card, LaTeX table and figure"
    )
    r.add_argument("--pool", required=True, help="baseline cache from `pace baseline`")
    r.add_argument("--logs", required=True, help="system log (calls and results)")
    r.add_argument("--system", default="mas")
    r.add_argument("--price-in", type=float, default=None)
    r.add_argument("--price-out", type=float, default=None)
    r.add_argument(
        "--k", type=int, default=None, help="use the first k samples per item"
    )
    r.add_argument("--n-boot", type=int, default=2000)
    r.add_argument("--perms", type=int, default=100)
    r.add_argument("--seed", type=int, default=0)
    r.add_argument("--json", default=None)
    r.add_argument("--latex", default=None)
    r.add_argument("--plot", default=None, help="vector figure path (.pdf)")
    r.add_argument(
        "--export-latex",
        default=None,
        help="write the nine-column rebuttal table for this run (LaTeX)",
    )
    r.add_argument(
        "--export-markdown",
        default=None,
        help="write the nine-column rebuttal table for this run (Markdown)",
    )
    r.add_argument(
        "--benchmark", default="n/a", help="benchmark label for the exported row"
    )
    r.add_argument(
        "--model-label", default="n/a", help="model label for the exported row"
    )
    r.add_argument(
        "--export-rollout-card",
        default=None,
        metavar="PREFIX",
        help="write PREFIX.json, PREFIX.yaml and PREFIX.tex: a PACE compute block for a rollout card (arXiv:2605.12131)",
    )
    r.add_argument(
        "--run-id",
        default="run",
        help="target id used in the rollout-card annotation rows",
    )
    r.set_defaults(func=_report)
    inf = sub.add_parser("inflate", help="beta-binomial sampling inflation: predicted accuracy of a K-sample vote from a pool of samples (CPU only)")
    inf.add_argument("--samples", required=True, help="JSONL, one row per sample with item and correct")
    inf.add_argument("--k", default="1,3,5,9,16,24", help="comma-separated vote sizes K to predict")
    inf.add_argument("--wrong-options", default=None, help="plurality model: number of wrong options W the wrong answers spread over (a number), or auto to estimate it from answer labels in the rows")
    inf.add_argument("--json", action="store_true")
    inf.set_defaults(func=_inflate)
    c = sub.add_parser(
        "classify",
        help="baseline rung (A to D) of a single-agent configuration given as JSON",
    )
    c.add_argument(
        "--config",
        required=True,
        help="JSON file; keys are listed in code/mae_eval/classifier.py",
    )
    c.set_defaults(func=_classify)
    u = sub.add_parser(
        "audit",
        help="one-screen diagnostic card for a run log (mas and sas calls) or a baseline configuration (JSON)",
    )
    u.add_argument(
        "input",
        help="JSONL run log with 'mas' and 'sas' calls, or a JSON baseline configuration",
    )
    u.add_argument(
        "--baseline-config",
        default=None,
        help="JSON configuration of the single-agent baseline, to classify its rung when INPUT is a log",
    )
    u.add_argument("--tolerance", type=float, default=0.05)
    u.add_argument("--price-in", type=float, default=None)
    u.add_argument("--price-out", type=float, default=None)
    u.add_argument("--json", action="store_true")
    u.add_argument(
        "--strict",
        action="store_true",
        help="exit with status 2 when the badge is a warning",
    )
    u.set_defaults(func=_audit)
    d = sub.add_parser(
        "dynamics",
        help="flip counts, tau rates, implied threshold, peer correlation, K_eff and tokens by round from a debate log",
    )
    d.add_argument(
        "log",
        help="JSONL with item, agent, round, correct (and optionally prompt_tokens, completion_tokens) per agent answer",
    )
    d.add_argument(
        "--null",
        default=None,
        help="optional no-communication control JSONL log to compute excess transition rates and excess peer correlation",
    )
    d.add_argument("--n-boot", type=int, default=1000)
    d.add_argument("--seed", type=int, default=0)
    d.add_argument("--first-round", type=int, default=None)
    d.add_argument("--last-round", type=int, default=None)
    d.add_argument("--json", action="store_true")
    d.set_defaults(func=_dynamics)
    i = sub.add_parser("import-logs", help="convert an external trace to PACE JSONL")
    i.add_argument(
        "--format", choices=["autogen", "langgraph", "crewai", "inspect", "lm-eval", "csv"], required=True
    )
    i.add_argument("--input", required=True)
    i.add_argument("--output", required=True)
    i.set_defaults(func=_import_logs)
    k = sub.add_parser("card", help="render a standalone PACE Card from PACE JSONL")
    k.add_argument("log")
    k.add_argument("--output", default=None)
    k.add_argument("--json", action="store_true")
    k.add_argument("--latex", action="store_true")
    k.add_argument("--format", choices=["json", "markdown", "latex"], default=None,
                   help="output format; with --v2, 'latex' is the PACE Card v1.0 table (the one the Studio and Workbench export), 'json' the v2 card, 'markdown' the v1 card in Markdown")
    k.add_argument("--v2", action="store_true", help="five-section PACE Evaluation Card (schema pace-card/v2) as JSON, or as a LaTeX snippet with --latex")
    k.set_defaults(func=_card)
    vl = sub.add_parser("validate-log", help="check a PACE JSONL trace: schema, duplicate call_id, parent_call_id cycles, zero-usage sentinel")
    vl.add_argument("log")
    vl.add_argument("--report", default=None, help="write the JSON report to this file")
    vl.add_argument("--json", action="store_true", help="print the JSON report instead of text")
    vl.add_argument("--strict", action="store_true", help="treat warnings as failures")
    vl.set_defaults(func=_validate_log)
    dc = sub.add_parser("doctor", help="self-check: Python and pace version, dependencies, the card schema and the framework adapters (exit 1 only for a missing core requirement)")
    dc.add_argument("--json", action="store_true", help="print the report as JSON")
    dc.set_defaults(func=_doctor)
    cp = sub.add_parser("compare", help="resource parity and directional verdict (CREDITS / RULES OUT / INCONCLUSIVE) of a candidate trace against a baseline trace")
    cp.add_argument("baseline")
    cp.add_argument("candidate")
    cp.add_argument("--format", choices=["json", "markdown", "latex"], default="markdown")
    cp.add_argument("--output", default=None)
    cp.add_argument("--tol", type=float, default=0.10, help="parity tolerance on the token ratio (default 0.10)")
    cp.add_argument("--margin", type=float, default=0.05, help="smallest accuracy advantage of interest that RULES OUT must exclude (default 0.05)")
    cp.add_argument("--min-items", type=int, default=20, help="fewest shared items needed to credit or rule out a candidate (default 20)")
    cp.add_argument("--fail-on-ruled-out", action="store_true", help="exit with code 1 when the verdict is RULES OUT (for CI gates)")
    cp.set_defaults(func=_compare)
    s = sub.add_parser("studio", help="open the zero-dependency PACE Studio")
    s.set_defaults(func=_studio)
    wb = sub.add_parser(
        "workbench", help="serve or export the standalone PACE Workbench"
    )
    wb.add_argument("--export-html", default=None)
    wb.add_argument("--serve", action="store_true")
    wb.add_argument("--host", default="127.0.0.1")
    wb.add_argument("--port", type=int, default=8765)
    wb.add_argument("--no-browser", action="store_true")
    wb.set_defaults(func=_workbench)
    cv7 = sub.add_parser("card-v7", help="render the seven-field PACE evaluation card")
    cv7.add_argument("log")
    cv7.add_argument("--baseline-log", default=None)
    cv7.add_argument("--latex", action="store_true")
    cv7.add_argument("--markdown", action="store_true")
    cv7.add_argument("--json", action="store_true")
    cv7.add_argument("--output", default=None)
    cv7.set_defaults(func=_card_v7)
    z = sub.add_parser(
        "pool-size", help="constructive token budget and recommended sample pool"
    )
    z.add_argument("--agents", type=int, required=True)
    z.add_argument("--rounds", type=int, required=True)
    z.add_argument("--prompt-tokens", type=float, required=True)
    z.add_argument("--msg-tokens", type=float, required=True)
    z.add_argument(
        "--topology",
        choices=["last_round_peers", "last_round_all", "full_history_echo"],
        default="last_round_peers",
    )
    z.add_argument("--json", action="store_true")
    z.set_defaults(func=_pool_size)
    sim = sub.add_parser("simulate", help="generate PACE theoretical simulation data")
    sim.add_argument(
        "--mode", choices=["voting", "debate", "scaffolding"], required=True
    )
    sim.add_argument("--items", type=int, default=100)
    sim.add_argument("--agents", type=int, default=5)
    sim.add_argument("--rounds", type=int, default=3)
    sim.add_argument("--p-mean", type=float, default=0.7)
    sim.add_argument("--rho", type=float, default=0.2)
    sim.add_argument("--choices", type=int, default=2)
    sim.add_argument("--regime", default="constant")
    sim.add_argument("--rate-a", type=float, default=0.25)
    sim.add_argument("--rate-b", type=float, default=0.15)
    sim.add_argument("--replicates", type=int, default=1)
    sim.add_argument("--verifier-fp", type=float, default=None)
    sim.add_argument("--verifier-fn", type=float, default=None)
    sim.add_argument("--budgets", type=float, nargs="*", default=[1000, 5000])
    sim.add_argument("--prompt-tokens", type=float, default=100)
    sim.add_argument("--msg-tokens", type=float, default=20)
    sim.add_argument("--seed", type=int, default=0)
    sim.add_argument("--out", default=None)
    sim.set_defaults(func=_simulate)
    meta = sub.add_parser("meta", help="native PACE meta-analysis (DerSimonian-Laird pooling; the paper's REML model is in analysis/run_k9_reml.py)")
    meta.add_argument("--contrasts", required=True)
    meta.add_argument(
        "--scale", choices=["log_or", "delta", "cohen_h"], default="log_or"
    )
    meta.add_argument("--phi", type=float, default=0.5)
    meta.add_argument("--rho-block", type=float, default=0.5)
    meta.add_argument("--category", default=None, help="keep only contrasts of this baseline category: A, B, C or BC (needs a category column, as in baseline_tier_contrasts.csv)")
    meta.add_argument("--covariance", action="store_true", help="also print the block covariance matrix (n x n; large for the full corpus)")
    meta.add_argument("--reml", action="store_true", help="three-level REML with CR2 intervals on log odds ratios (the paper's model; default selection Category B/C reproduces beta = -0.195); needs numpy, pandas, scipy")
    meta.add_argument("--json", action="store_true")
    meta.set_defaults(func=_meta)
    power = sub.add_parser("power", help="prospective PACE power analysis")
    power.add_argument("--p-base", type=float, default=None)
    power.add_argument("--delta", type=float, default=None)
    power.add_argument("--ledger", default=None, help="contrast ledger CSV (study,category,key,d,p_base,n): audit every Category A gain against its own minimum detectable effect")
    power.add_argument("--phis", type=float, nargs="*", default=[0.3, 0.5, 0.7], help="phi values for --ledger")
    power.add_argument("--n-items", type=int, default=None)
    power.add_argument("--power", type=float, default=0.8)
    power.add_argument("--alpha", type=float, default=0.05)
    power.add_argument("--phi", type=float, default=0.5)
    power.add_argument("--shared-arms", type=int, default=1)
    power.add_argument("--json", action="store_true")
    power.set_defaults(func=_power)
    bench = sub.add_parser(
        "benchmark-gen", help="generate escape-route benchmark fixtures"
    )
    bench.add_argument(
        "--route",
        choices=["clue_grid", "distributed_code", "verifier_curve"],
        required=True,
    )
    bench.add_argument("--items", type=int, default=30)
    bench.add_argument("--agents", type=int, default=3)
    bench.add_argument("--seed", type=int, default=42)
    bench.add_argument("--epsilons", type=float, nargs="*", default=[0.01, 0.05, 0.1])
    bench.add_argument("--out", required=True)
    bench.set_defaults(func=_benchmark_gen)
    open_cmd = sub.add_parser("aggregate-open", help="aggregate open-ended samples")
    open_cmd.add_argument("--input", required=True)
    open_cmd.add_argument(
        "--metric",
        choices=["ngram_cosine", "token_jaccard", "sequence_ratio", "code_structural"],
        default="ngram_cosine",
    )
    open_cmd.add_argument("--out", default=None)
    open_cmd.set_defaults(func=_aggregate_open)
    plot = sub.add_parser("plot", help="write a pure SVG diagnostic figure")
    plot.add_argument(
        "--kind", choices=["waterfall", "phase", "frontier", "influence"], required=True
    )
    plot.add_argument("--input", default=None, help="report/card JSON (waterfall, frontier, influence)")
    plot.add_argument("--p-greedy", type=float, default=None, help="waterfall: greedy single-pass accuracy (with --p-sampled and --p-mas instead of --input)")
    plot.add_argument("--p-sampled", type=float, default=None, help="waterfall: sampled-baseline accuracy")
    plot.add_argument("--p-mas", type=float, default=None, help="waterfall: multi-agent accuracy")
    plot.add_argument("--out", required=True)
    plot.set_defaults(func=_plot)
    h = sub.add_parser(
        "hidden-profile",
        help="generate synthetic split-evidence (hidden-profile) items and check their validity",
    )
    h.add_argument("--n", type=int, default=100, help="number of items")
    h.add_argument("--agents", type=int, default=5)
    h.add_argument("--criteria", type=int, default=10, help="total number of criteria")
    h.add_argument(
        "--split",
        type=int,
        default=6,
        help="number of criteria divided among the agents (the rest are shared)",
    )
    h.add_argument(
        "--margin",
        type=int,
        default=3,
        help="score gap per criterion between the favoured and the disfavoured candidate (at least 2)",
    )
    h.add_argument("--seed", type=int, default=42)
    h.add_argument("--format", choices=["text", "numeric"], default="text")
    h.add_argument(
        "--out", default=None, help="output JSONL (default: standard output)"
    )
    h.set_defaults(func=_hidden_profile)
    f = sub.add_parser(
        "frontier",
        help="self-consistency frontier of a sample pool, optionally with system points from a run log",
    )
    f.add_argument(
        "--samples",
        required=True,
        help="baseline cache from `pace baseline` (greedy + sampled completions per item)",
    )
    f.add_argument(
        "--logs",
        default=None,
        help="run log; every value of its 'system' field is drawn as a point",
    )
    f.add_argument("--k", type=int, default=None)
    f.add_argument("--perms", type=int, default=100)
    f.add_argument("--seed", type=int, default=0)
    f.add_argument(
        "--estimator",
        choices=["isotonic", "envelope", "crossfit", "directional"],
        default="isotonic",
        help="frontier estimator: isotonic (PAVA), envelope (upper bound), crossfit (2-fold lower bound), or directional (both)",
    )
    f.add_argument(
        "--claim-direction",
        choices=["auto", "positive", "nonpositive"],
        default="auto",
        help="claim direction when --estimator directional is used",
    )
    f.add_argument(
        "--n-splits",
        type=int,
        default=200,
        help="2-fold random item splits for crossfit frontier estimation",
    )
    f.add_argument("--json", default=None)
    f.add_argument("--out", default=None, help="figure path (.pdf vector, or .png)")
    f.set_defaults(func=_frontier)
    t = sub.add_parser(
        "rebuttal",
        help="nine-column rebuttal table from a contrasts CSV (default: outputs/baseline_tier_contrasts.csv, or data/baseline_tier_contrasts.csv in the release tree)",
    )
    t.add_argument(
        "--contrasts",
        "--data",
        dest="contrasts",
        default="outputs/baseline_tier_contrasts.csv",
        help="contrasts CSV with columns study, category (rung), baseline, key 'Study|bench|model|arm', p_base, p_mas",
    )
    t.add_argument("--study", default=None)
    t.add_argument("--export-latex", default=None)
    t.add_argument("--export-markdown", default=None)
    t.set_defaults(func=_rebuttal)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
