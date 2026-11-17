# Live validation suite (`scripts/run_12hr_live_suite.py`)

Unattended, resumable, local Ollama models only (no paid API, no downloads). Exploratory; it implements the exploratory arms of `docs/PREREGISTRATION_ADDENDUM_2.md` and changes nothing in the confirmatory plan.

```bash
python scripts/run_12hr_live_suite.py --dry-run                       # the plan and the stop time
python scripts/run_12hr_live_suite.py --stop-at 06:00 --workers 2     # run; every finished item is checkpointed
python scripts/run_12hr_live_suite.py --only report                   # rebuild the report from what exists
```

**Resume.** Every cell directory under `outputs/experiments/live_validation/` has `calls.jsonl` (a cache of every model call) and `results.jsonl` (one row per finished item and arm). A rerun skips finished items and reuses cached calls, so a crash or a timeout loses at most the call in flight. `progress.json` shows the phase, the items finished per cell, and the arms deferred.

**Call log.** `calls.pace.jsonl` has one record per attempt: `call_id` (`key#attempt`), `parent_id` (the same agent's call in the previous round, or null), `strategy`, `item`, `round`, `agent`, `model`, `started_at`, `ended_at`, `seconds`, `input_tokens`, `output_tokens`, `reasoning_tokens` (null unless the server reports it; never inferred), `think_block_chars` (characters inside `<think>` blocks of the text), `thinking_chars` (server-reported thinking field), `retry`, `status` (`ok`, `timeout`, `error`) and `error`. Per-call timeout 120 s; at most 2 retries; every failed attempt is logged, and an item whose call still fails goes to `errors.jsonl` and is skipped, never filled in.

**Phases** (hour budgets; a phase ends at its budget or when its items are done; work stops 25 minutes before the stop time so the report is ready then): smoke (hour 1), GSM8K (hours 2 to 4), MATH-500 level 5 (hours 5 to 7), hidden profile 2x2 (hours 8 and 9), Route II verifier gating (hour 10), placebo controls (hour 11), report (hour 12). Heterogeneous arms (llama3.1:8b, qwen2.5:14b-instruct, qwen2.5-coder:14b) need other models and are deferred while the GPU is shared with the confirmatory batch, then attempted at the end if the GPU is free.

**What it cannot do here.** There is no `pace` command in this script; analysis uses the `cme` modules. GPQA is gated and is not used. While the confirmatory batch occupies the GPU, calls are several times slower than on an idle GPU (measured in the smoke run in `suite.log`), so the items finished per cell will be fewer than planned, and the report lists the numbers finished. Raising `--workers` or `--allow-concurrent` speeds the suite and slows the confirmatory batch.
