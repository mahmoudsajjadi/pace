# Phase 2 pilot report (interim, 2026-11-11)

Status (updated 2026-11-12): **the greedy headroom pilot is complete for llama3.1:8b, qwen3:14b, gemma4:12b, olmo-3:7b and deepseek-r1:14b on five tasks, and for qwen2.5-coder:7b on MBPP** (`scripts/phase2_greedy_pilot.py`, log in `outputs/experiments/pilot_greedy/progress.log`). The first confirmatory batch (llama3.1:8b, hidden-profile control then MMLU-Pro) was launched from commit 6b508fd; see `outputs/experiments/confirmatory/MANIFEST.jsonl`. Regenerate the table at any time with `python scripts/summarize_pilot.py`, which re-scores the cached calls and never calls a model. Nothing here is a confirmatory result; these are pilots for the headroom check and cost estimates, as specified in `docs/PHASED_EXPERIMENT_AND_TOOL_ROADMAP.md` section 2.

## What exists

| Piece | Path | Evidence |
|---|---|---|
| Strategies 1-9, shared round 1, resumable call store | `code/cme/experiment.py` | `tests/test_cme_experiment.py` (14 tests, mock client) |
| Task loaders and scorers (MMLU-Pro, MATH-500 levels 4-5, MuSiQue 4-hop, MBPP, synthetic split-evidence control) | `code/cme/tasks.py` | same tests; data cached under `data/experiments/` (git-ignored, public datasets via the Hugging Face datasets-server API) |
| Real calls | `outputs/experiments/pilot_greedy/*/calls.jsonl`, `outputs/experiments/timing_probe/*/calls.jsonl` | every call: tokens, latency, seed, temperature, model digest |

Substitutions to state in any write-up: plain MBPP (500 test items, `test_list` asserts) replaces MBPP+; the positive control is a synthetic hidden-profile task generated here (seed 42), not a published benchmark; Strategy 3 ("more thinking") uses Ollama's `think` flag for qwen3 and deepseek-r1 and an extended-reasoning prompt (4,096 token cap) for the other models, and these are different manipulations.

## Strategy 1 headroom check (greedy, 50 items per task, seed 42, max 2,048 tokens)

Scored with the final scorer (an `Answer:` line, else the last `\boxed{}`, else "the answer is ..."). The first run used `Answer:` only and scored MATH at 0.20; 29 of 50 responses had no `Answer:` line but a `\boxed{}` answer, so the scorer was changed and all cached calls re-scored (no new calls).

| Model | Task | Greedy acc. | In 40-75% band? | No parsable answer | Truncated at max tokens | s/call |
|---|---|---|---|---|---|---|
| llama3.1:8b | MMLU-Pro (50) | 0.42 | yes | 6 | 7 | 9.6 |
| llama3.1:8b | MATH-500 L4-5 (50) | 0.38 | no, below | 4 | 4 | 9.4 |
| llama3.1:8b | MuSiQue 4-hop (50) | 0.34 | no, below | 2 | 2 | 6.5 |
| llama3.1:8b | split-evidence control, full evidence (50) | 0.92 | no, above | 0 | 0 | 5.8 |
| llama3.1:8b | MBPP (50) | 0.54 | yes | 0 | 0 | 3.2 |

Model digest recorded for llama3.1:8b: `46e0c10c039e` (first 12 characters). With 50 items the 95% interval on an accuracy near 0.4 is about +/-0.14, so "below 40%" for MATH (0.38) and MuSiQue (0.34) is not distinguishable from the band edge; the control task at 0.92 with full evidence is expected (a single agent that sees all scores can add them). The other four models will be added to this table when their runs finish; per the roadmap, full runs wait until that check is read.

## Measured cost per item by strategy (llama3.1:8b, MMLU-Pro, 2 items; counts are exact, accuracy on 2 items means nothing)

| Strategy | Calls/item | Prompt tok | Completion tok | Serial s/item |
|---|---|---|---|---|
| S1 greedy | 1 | 182 | 164 | 7.0 |
| S2 pool, k=16 | 16 | 2,920 | 8,907 | 142 |
| S3 extended-reasoning prompt | 1 | 200 | 2,084 | 28 |
| S4 vanilla debate (5 agents, 3 rounds) | 15 (10 new after the pool) | 10,501 | 5,836 | 106 |
| S5 confidence-weighted debate | 15 | 10,767 | 6,070 | 109 |
| S7 placebo debate | 15 | 10,740 | 8,343 | 139 |
| S8 mixture-of-agents (2 layers) | 11 | 6,631 | 5,585 | 93 |

Per item the full suite (S1-S8, shared round 1) is about 64 new calls. Projected serial wall time on one local 8B model at n=1,000 is roughly 2 h (S1) to 54 h (S7) per strategy, so a full local run at the roadmap's item counts is not feasible serially; it needs parallel slots (`OLLAMA_NUM_PARALLEL`), smaller n, or hosted endpoints. Token counts at $2/$10 per million are illustrative only (those prices are from the roadmap and are not verified). Local cost is electricity, not dollars. Ollama's `prompt_eval_count` can exclude prompt tokens served from its KV cache, so prompt tokens may be undercounted on repeated prefixes.

## Positive-control sanity check (llama3.1:8b, 6 synthetic items, pipeline check only)

| Arm | Calls/item | Accuracy |
|---|---|---|
| S2 pool, full evidence, plurality | 16 | 0.83 |
| S2v independent agents on split evidence, plurality (no communication) | 5 | 0.00 |
| S4 debate on split evidence | 15 | 0.83 |

The task behaves as designed (independent voting over partial views picks the decoy; exchanging messages recovers the answer), which is what a positive control needs. Six items cannot support any claim; the 300-500 item run is the test.

## Not done

- Strategy 6 (heterogeneous debate) and Strategy 9 (verifier) are implemented and unit-tested with a mock client but have not been run on a real model.
- Hosted-model pilots (gpt-oss, frontier tiers) were not started: no hosted endpoint was configured and no spend was authorised.
- No full runs, no preregistration and no confirmatory statistics: the 40-75% check for the remaining models is still pending.

## All-model greedy table (update 2026-11-12; 50 items per cell, max 2,048 tokens)

| Model | Task | n | Greedy acc. | Headroom (40-75%) | No parsable answer | Truncated at max tokens | Prompt tok/call | Completion tok/call | s/call | Digest |
|---|---|---|---|---|---|---|---|---|---|---|
| deepseek-r1:14b | hidden_profile | 50 | 0.80 | above 75% | 10 | 10 | 489 | 1753 | 47.6 | c333b7232bdb |
| deepseek-r1:14b | math500_l45 | 50 | 0.52 | in band | 19 | 19 | 104 | 1452 | 39.3 | c333b7232bdb |
| deepseek-r1:14b | mbpp | 50 | 0.48 | in band | 0 | 25 | 83 | 1536 | 41.3 | c333b7232bdb |
| deepseek-r1:14b | mmlu_pro | 50 | 0.60 | in band | 16 | 16 | 236 | 1351 | 36.9 | c333b7232bdb |
| deepseek-r1:14b | musique_4hop | 50 | 0.24 | below 40% | 17 | 17 | 2649 | 1296 | 39.7 | c333b7232bdb |
| gemma4:12b | hidden_profile | 50 | 0.00 | below 40% | 50 | 50 | 485 | 2048 | 43.8 | 4eb23ef187e2 |
| gemma4:12b | math500_l45 | 50 | 0.04 | below 40% | 48 | 48 | 117 | 2016 | 42.6 | 4eb23ef187e2 |
| gemma4:12b | mbpp | 50 | 0.20 | below 40% | 0 | 40 | 101 | 1771 | 37.5 | 4eb23ef187e2 |
| gemma4:12b | mmlu_pro | 50 | 0.10 | below 40% | 45 | 45 | 251 | 1950 | 41.4 | 4eb23ef187e2 |
| gemma4:12b | musique_4hop | 50 | 0.00 | below 40% | 50 | 50 | 2625 | 2048 | 45.8 | 4eb23ef187e2 |
| llama3.1:8b | hidden_profile | 50 | 0.92 | above 75% | 0 | 0 | 488 | 289 | 5.8 | 46e0c10c039e |
| llama3.1:8b | math500_l45 | 50 | 0.38 | below 40% | 4 | 4 | 107 | 590 | 9.4 | 46e0c10c039e |
| llama3.1:8b | mbpp | 50 | 0.54 | in band | 0 | 0 | 87 | 84 | 3.2 | 46e0c10c039e |
| llama3.1:8b | mmlu_pro | 50 | 0.42 | in band | 6 | 7 | 228 | 607 | 9.6 | 46e0c10c039e |
| llama3.1:8b | musique_4hop | 50 | 0.34 | below 40% | 2 | 2 | 2531 | 276 | 6.5 | 46e0c10c039e |
| olmo-3:7b | hidden_profile | 50 | 0.00 | below 40% | 50 | 50 | 534 | 2048 | 29.0 | b8d4c92ac9c1 |
| olmo-3:7b | math500_l45 | 50 | 0.12 | below 40% | 43 | 43 | 153 | 1958 | 26.8 | b8d4c92ac9c1 |
| olmo-3:7b | mbpp | 50 | 0.10 | below 40% | 0 | 33 | 133 | 1755 | 24.0 | b8d4c92ac9c1 |
| olmo-3:7b | mmlu_pro | 50 | 0.26 | below 40% | 36 | 36 | 274 | 1763 | 24.5 | b8d4c92ac9c1 |
| olmo-3:7b | musique_4hop | 50 | 0.14 | below 40% | 40 | 40 | 2582 | 1893 | 32.8 | b8d4c92ac9c1 |
| qwen2.5-coder:7b | mbpp | 50 | 0.80 | above 75% | 0 | 0 | 109 | 127 | 3.7 | dae161e27b0e |
| qwen3:14b | hidden_profile | 50 | 1.00 | above 75% | 0 | 0 | 502 | 590 | 17.6 | bdbd181c33f2 |
| qwen3:14b | math500_l45 | 50 | 0.36 | below 40% | 4 | 4 | 117 | 732 | 21.3 | bdbd181c33f2 |
| qwen3:14b | mbpp | 50 | 0.70 | in band | 0 | 1 | 96 | 109 | 5.1 | bdbd181c33f2 |
| qwen3:14b | mmlu_pro | 50 | 0.70 | in band | 4 | 4 | 248 | 581 | 17.3 | bdbd181c33f2 |
| qwen3:14b | musique_4hop | 50 | 0.32 | below 40% | 0 | 0 | 2662 | 138 | 8.0 | bdbd181c33f2 |

Reading of the table (pilot only; 50 items, intervals about ±0.14):
- gemma4:12b and olmo-3:7b: 36 to 50 of 50 responses hit the 2,048-token cap on four of five tasks and no answer could be extracted (accuracy 0.00 to 0.26 except MBPP 0.20 and 0.10). They are excluded from the multi-agent runs; a larger cap was not tried, so this describes behaviour at this cap and prompt, not model quality.
- deepseek-r1:14b: 16 to 19 of 50 responses were truncated on MATH, MMLU-Pro and MuSiQue (25 of 50 on MBPP) at 2,048 tokens, at 37 to 48 s per call and 1,300 to 1,750 completion tokens. Its greedy accuracies (MATH 0.52, MMLU-Pro 0.60) are therefore lower bounds, and a confirmatory run needs a much larger cap (8,192 is pre-set for the think arm) and more wall time than the other models.
- qwen3:14b (thinking off for S1): MMLU-Pro 0.70, MBPP 0.70 in band; MATH 0.36 and MuSiQue 0.32 just below; control task 1.00.
- qwen2.5-coder:7b on MBPP: 0.80, above the 75% band, so headroom for sampling and debate is smaller than the plan assumed.

## Confirmatory launch (2026-11-12)

Parallel execution (`--workers`) was measured on the local server before use: 8 short requests took 30.4 s serially, 18.6 s at 2 workers and 15.3 s at 4 workers (36, 60 and 72 tokens per second), so the gain is about 1.6x at 2 workers and 2.0x at 4. In the first confirmatory minutes the llama3.1:8b batch ran at roughly 0.17 calls per second. At that rate tier 1 (strategies 2 and 4 on the control; 2, 3, 4 and 8 on MMLU-Pro) is about 17,000 calls, roughly 28 hours, and the complete llama plan about two days, before qwen3:14b. These are extrapolations from the first minutes, not measurements of the full run.
