# cme: measure a multi-agent system against the self-consistency frontier

`pace` answers one question: at the token cost your system actually used, does it beat what plain sampling plus voting would reach on the same items? It builds on `mae_eval` (resource vector and parity auditor). Status: prototype v0.1; no results from it are in the paper yet.

## 60-second quickstart

Needs Python 3.9+, `numpy` (and `matplotlib` for the figure) and any OpenAI-compatible server, for example Ollama.

```bash
cd code
export PYTHONPATH=.            # or: pip install -e .

# 1. Greedy run + 16 sampled completions per item (cached; rerun the same command to resume)
python -m pace baseline --model llama3.1:8b --bench my_items.jsonl --k 16 --out pool.jsonl
#    my_items.jsonl: one {"id": ..., "question": ..., "answer": ...} per line. `--bench toy` is a synthetic smoke test.

# 2. Log your multi-agent system with no code changes: point its base URL at the proxy
python -m pace proxy --upstream http://localhost:11434/v1 --log run.jsonl --price-in 0 --price-out 0 &
#    send X-PACE-Item: <item id> (and optionally X-PACE-Round / X-PACE-Agent / X-PACE-System) headers; write one
#    {"system": "mas", "item": "<id>", "correct": true} line per item to run.jsonl when you score the final answers

# 3. Report
python -m pace report --pool pool.jsonl --logs run.jsonl --latex card.tex --plot frontier.pdf --json report.json
```

The report prints accuracy, the isotonic self-consistency frontier at the system's mean tokens, the frontier gap with a paired bootstrap 95% interval over items, and MAS/SAS resource ratios (`n/a` when both sides are 0 or one side is unreported).

## Python API

```python
from pace import build_report, frontier_gap, to_latex
rep = build_report("pool.jsonl", "run.jsonl", n_boot=2000)
print(rep["frontier_gap"])
```

## Instrument a Python client without a proxy: `pace.wrap`

```python
import pace
from openai import OpenAI

client = pace.wrap(OpenAI(), log_path="pace_trace.jsonl", price_in=0.0, price_out=0.0)   # prices: USD per million tokens, or omit for cost = null
with pace.track(item_id="item_042", system="mas", agent="agent_1", round=2):
    response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": "..."}])
pace.log_result("pace_trace.jsonl", "item_042", correct=True, system="mas")   # once per item, after scoring
```

`wrap` forwards everything to the wrapped client and logs one line per `chat.completions.create` / `completions.create` call (sync or async) or top-level `completion` (litellm-style), in the same format as `pace proxy`, so `pace report --pool pool.jsonl --logs pace_trace.jsonl` reads it. `track` labels calls made inside the block (blocks nest; labels are per thread or task). Not covered in v0.1: streaming (raises `ValueError`; usage is unknown at return and is never estimated), calls made through `with_raw_response`, and responses without a usage block (logged with `usage_missing: true`).

## One-screen audit: `pace audit`

```bash
python -m pace audit run_trace.jsonl --baseline-config sas.json     # run log with "mas" and "sas" calls; sas.json: {"n_samples": 1}
python -m pace audit sas.json                                        # a baseline configuration alone
```

The card shows the baseline rung (A to D, rules in `code/mae_eval/classifier.py`), the measured MAS/SAS ratios R_token, R_lat and R_cost (cost needs `--price-in/--price-out`), token parity within `--tolerance`, a badge, and a BibTeX entry (the manuscript is in preparation, so the entry is `@unpublished`). The badge is `PASS: COMPUTE-MATCHED` only when token parity holds and the baseline is rung C or D, or when a configuration alone declares a matched resource (R2) or a sweep (R1); everything else prints `WARNING: BASELINE NOT COMPUTE-MATCHED`. A rung A or B baseline is not wrong; the warning says the comparison does not separate coordination from extra computation. `--strict` exits with status 2 on a warning.

Integration recipes in `examples/`: `openai_quickstart.py` (runs against a fake client in the tests), `langgraph_integration.py` and `crewai_integration.py` (written from the public APIs; not run here because those packages are not installed).

## Debate dynamics: `pace dynamics`

```bash
python -m pace dynamics debate_log.jsonl --n-boot 1000      # one JSON line per agent answer: item, agent, round, correct [, prompt_tokens, completion_tokens]
```

Prints flip counts between the first and last round, tau_ic (wrong to right) and tau_ci (right to wrong), the implied threshold p_star_hat = tau_ic / (tau_ic + tau_ci), first- and last-round accuracy, `rho_total` (the intraclass correlation of correctness across the agents of an item, per round, which includes shared item difficulty; the JSON also keeps its earlier name `rho_peer`) with K_eff = K / (1 + (K - 1) rho_total), `delta_rho_debate` = rho_total(last round) - rho_total(first round) (the excess correlation induced by debate, in which shared item difficulty largely cancels), and mean tokens per call by round, each with a 95% percentile interval from a bootstrap over items. The rates assume the constant-rate model of the paper, and the command does not test that model.

## Hidden-profile task generator: `pace hidden-profile`

```bash
python -m pace hidden-profile --n 100 --agents 5 --criteria 10 --split 6 --margin 3 --seed 42 --format text --out hp.jsonl
```

Writes synthetic split-evidence items (shared criteria favour a decoy, split criteria favour the target) and checks them from the generated scores: the decoy must strictly lead every single view, the target must strictly lead the pooled evidence, and every split criterion must be seen by some agent. Infeasible knobs are rejected, and a failed check writes nothing. With the defaults the prompts, views and answers equal those of the released 500-item file. `--format numeric` shows the scores as a CSV table.

## What it does not do (v0.1)

- The proxy rejects `"stream": true` requests.
- Reasoning tokens are logged only when the endpoint reports them; nothing is inferred.
- Prices are never bundled; pass `--price-in/--price-out` (USD per million tokens) or cost stays unreported.
- Answer matching is exact after light normalisation (last `Answer:` line); use your own scorer for free-form tasks and write the `correct` flags yourself.
- The frontier uses plurality voting over random k-subsets of the pool and linear interpolation in tokens; beyond the pool's token range the report says `beyond range` and the gap is an upper bound.

Tests: `pytest tests/test_pace.py` (reference pools with hand-computed answers, resume behaviour, proxy against a fake upstream).
