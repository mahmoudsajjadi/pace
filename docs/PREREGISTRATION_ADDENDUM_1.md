# Addendum 1 to the preregistration draft (2026-11-12)

Status: draft, not registered on OSF. This file does not edit `docs/PREREGISTRATION.md`: the SHA-256 recorded in `outputs/experiments/confirmatory/MANIFEST.jsonl` for the llama3.1:8b runs (`826cbe97…`) refers to that file as committed in `6b508fd`. Where the two disagree, this addendum supersedes the original from the date above, and the manifest hash of each later run shows which version of the code ran.

## Author decisions recorded

1. **Data collection order.** The running batch is kept running; the claim made for it is "preregistered before outcome analysis" (the draft and its hash were committed before any confirmatory call, and no outcome has been analysed).
2. **Primary cells approved.** llama3.1:8b on MMLU-Pro (H1, H3, H4) and llama3.1:8b on the hidden-profile control (H2). All other cells are replications.
3. **Reporting of precision.** Confirmatory results are reported as the paired bootstrap 95% interval with Holm correction, with a sentence of the form "the interval excludes coordination advantages larger than +X percentage points" (X is the upper limit). No point null at δ = 0.02 is asserted at n = 250 or 200.
4. **MATH-500 levels 4–5 is retained as a secondary, exploratory replication cell** and is labelled "restricted headroom" (pilot greedy 0.36–0.38 for llama3.1:8b and qwen3:14b, at the lower end of the 40–75% band). It is outside the Holm family.

## Changes to the design

5. **MMLU-Pro item sampling corrected before any MMLU-Pro confirmatory call.** The first loader drew ten contiguous 100-row blocks from a split that is ordered by category, so its 1,000-row pool contained 6 of the 14 categories. The loader now draws 40 seeded blocks over the whole split (about 4,000 rows, seed 42); 250 items from the new pool cover 13 of 14 categories. Consequences: (a) the MMLU-Pro items differ from the pilot items, so the "first 50 confirmatory items are pilot items" statement in section 3 of the original draft no longer holds for MMLU-Pro and the planned sensitivity analysis that excludes pilot items is not needed for that task; (b) the pilot greedy accuracies for MMLU-Pro (llama3.1:8b 0.42, qwen3:14b 0.70, deepseek-r1:14b 0.60 with truncation) were measured on the old 6-category items and are kept only as headroom evidence. Hidden-profile items are unchanged (generator, seed 42).
6. **Targeted `deepseek-r1:14b` runs (replace the MATH and MMLU-Pro N = 250 allocation for this model).** One worker, `--max-tokens 8192`, context 12,288, Ollama `think` flag on so that thinking is reported separately.
   - Hidden-profile control, N = 50: S2v (independent thinking agents on split views, plurality vote), S4 (debate on split views), S1 (single agent with full evidence). Question: does extended thinking by independent agents recover the hidden profile, or does recovery still need communication?
   - MMLU-Pro, N = 50, drawn round-robin over categories (13 of 14 present in the pool): S1 and S4.
   These runs are exploratory and outside the Holm family.
7. **Reasoning share.** Ollama does not report reasoning tokens and none are inferred. The share is computed on characters: R_reason / (R_reason + R_comm) with R_reason the characters of the thinking field returned by the server, and R_comm the characters of peer messages shown in debate prompts (`comm_chars`, recorded per call from commit `1915570`). It is a proxy for the token ratio and is labelled as such.
8. **Code changes after the first launch** (all defaults unchanged, so the llama3.1:8b runs behave as before): an optional `think` default for ordinary calls, per-call `prompt_chars` and `comm_chars` fields, strategy 10 (split-evidence vote without the 16-sample pool), `--num-ctx`, and `--stratify`. Calls made before commit `1915570` do not have the two character fields.

## Pilot facts added since the draft

- qwen2.5-coder:7b scores 0.80 greedy on MBPP (50 items), above the 75% band; MBPP headroom for sampling or debate is therefore limited for that model.
- The all-model pilot table is in `docs/PHASE2_PILOT_REPORT.md`.
