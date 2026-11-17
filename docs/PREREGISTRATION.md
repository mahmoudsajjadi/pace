# Preregistration draft: debate, sampling and extended thinking at measured token cost

**Status: DRAFT for the author's review. Not registered on OSF.** Nothing has been uploaded. Registration is an external action and needs the author's approval. A registration only counts as preregistered for data collected after its timestamp: data collection for the confirmatory batches was started from the git commit that carries this file (hash in `outputs/experiments/confirmatory/MANIFEST.jsonl`) before an OSF timestamp exists, so unless the author registers this file first and discards or labels the earlier runs, the OSF record can claim only "registered during data collection, before any outcome analysis". No outcome has been analysed at the time of writing.

Template: OSF Standard Pre-Registration (sections follow its headings). Companion documents: `docs/PHASED_EXPERIMENT_AND_TOOL_ROADMAP.md` (design source), `protocol/PROSPECTIVE_PILOT_PROTOCOL.md` (earlier draft with the author's δ = 0.02 and seed 42), `docs/PHASE2_PILOT_REPORT.md` (pilot data).

## 1. Study information

**Title.** Do multi-agent debate, repeated sampling and extended thinking differ at equal measured token cost? A controlled comparison with local open-weight models.

**Description.** Eight inference strategies are run on the same items with the same model: greedy, a pool of 16 independent samples (self-consistency), one call with more thinking, vanilla debate, confidence-weighted debate, placebo debate, a mixture-of-agents aggregator, and (for code) a verifier arm. The first five samples of the pool are also round 1 of every debate and aggregator arm, so debate and voting differ only by the messages. A synthetic hidden-profile task, built so that the evidence is split across agents, is the positive control.

**Hypotheses.** Let F(t) be the self-consistency frontier (section 5.1) and gap(s) = accuracy(s) minus F(measured mean tokens of s), estimated on the same items.

- **H1.** Vanilla homogeneous debate (S4) has gap(S4) ≤ 0 on MMLU-Pro.
- **H2.** On the hidden-profile positive control, debate over split evidence (S4 with views) has gap > 0 against the frontier built from independent agents that see the split evidence (S2v, plurality, no communication).
- **H3.** Ordering at matched measured tokens of the three scaling routes. Sampling is the reference (gap 0 by construction), so the test is gap(S3, more thinking) versus gap(S4, more agents): the sign of gap(S4) − gap(S3) on MMLU-Pro.
- **H4.** Directional replication of Wunderlich et al. at smaller scale: on MMLU-Pro, mixture-of-agents (S8) and debate (S4) have gap > 0 against self-consistency at comparable tokens. This is not an exact replication: that paper uses Llama 3.1 70B, 10 self-consistency iterations, debate with 4 agents and 2 layers, and mixture-of-agents with 5 proposers and 4 layers (single-proposer setting), with compute measured as theoretical runtime read off Pareto fronts.

## 2. Design plan

**Type.** Within-item experiment: every strategy is applied to every item of a task with the same model; comparisons are paired over items.
**Blinding.** None; scoring is automatic.
**Randomisation.** Item subsets are drawn once with seed 42 from the filtered public pool. Per-call sampling seeds are the first 8 hex digits of SHA-256 over (base seed 0, call key), so they are distinct per (item, strategy, agent, round, sample index) and reproducible. Sampled arms use temperature 0.7; greedy and S3 use temperature 0.
**Software and models.** Ollama 0.40.13 on one RTX 4070 (12 GB), context 8,192 tokens; every call records the model digest. Models: `llama3.1:8b` (digest 46e0c10c039e…), `qwen3:14b` (bdbd181c33f2…), `deepseek-r1:14b` (c333b7232bdb…), `qwen2.5-coder:7b` (MBPP only).

## 3. Sampling plan

**Existing data.** A 50-item greedy pilot per (model, task) and small timing probes exist (`outputs/experiments/pilot_greedy/`, `outputs/experiments/timing_probe/`). They informed the choice of models, tasks and item counts, and the scorer (an `Answer:` line, else the last boxed expression, else "the answer is ..."). The first 50 confirmatory items of each task are the pilot items; a sensitivity analysis excludes them. Pilot accuracies are in the pilot report; no multi-agent outcome has been analysed.
**Excluded models.** `gemma4:12b` and `olmo-3:7b`: 36 to 50 of 50 greedy responses hit the 2,048-token cap on four of five tasks, so answers could not be extracted. This is a pilot-based decision and is reported.
**Item counts (pre-set, limited by local compute).** MMLU-Pro 250 (llama3.1:8b, qwen3:14b, deepseek-r1:14b); MATH-500 levels 4–5, 200 (qwen3:14b, deepseek-r1:14b); MBPP 200 (llama3.1:8b, qwen2.5-coder:7b); hidden-profile control 200 (llama3.1:8b, qwen3:14b).
**Precision.** With per-item paired differences of standard deviation up to 0.5, the half-width of a 95% interval is about ±0.062 at n = 250 and ±0.069 at n = 200. The author's equivalence margin δ = 0.02 therefore cannot be resolved at these sizes. Confirmatory claims are of the form "the interval excludes effects larger than its upper limit"; a result inside (−δ, +δ) is not expected and "no difference" is not claimed from an interval wider than that.
**Stopping rule.** Fixed n; no interim analysis. Items with an unrecoverable call error after 3 retries are dropped and counted.
**Primary cells.** The confirmatory family uses one primary cell per hypothesis: llama3.1:8b on MMLU-Pro (H1, H3, H4) and llama3.1:8b on the hidden-profile control (H2). All other model × task cells are pre-specified replications, reported with unadjusted intervals and labelled as such.

## 4. Variables

**Manipulated.** Strategy S1–S9 (section 1 of the roadmap): S1 greedy; S2 pool of 16 samples; S3 more thinking (Ollama `think` flag for qwen3 and deepseek-r1, an extended-reasoning prompt with a 4,096-token cap for llama3.1:8b; these are different manipulations and are not pooled across models); S4 vanilla debate (5 copies, 3 rounds, round 1 = pool samples 0–4, peers' last 800 characters shown); S5 confidence-weighted debate; S6 debate among different models with a same-mix vote (S6v); S7 placebo debate (peer messages replaced by unrelated text of the same length from another item's pool); S8 two-layer mixture-of-agents; S9 verifier (MBPP only).
**Measured.** Correctness (code: all `test_list` asserts pass), plurality or weighted vote with ties sharing credit, prompt tokens, completion tokens (reasoning tokens only when the endpoint reports them; Ollama does not, so thinking characters are recorded instead), wall time per call, cost (local calls: 0 API dollars, electricity not priced), seed, temperature, model digest. Max tokens per call 4,096 (8,192 for S3 with the think flag).
**Indices.** Tokens of a strategy are prompt plus completion tokens of all calls it used, including the reused round-1 calls. Borrowed placebo text is not charged. Ollama's prompt count can omit KV-cache hits; a sensitivity analysis uses completion tokens only.

## 5. Analysis plan

**5.1 Estimand.** Pool accuracy for k = 1…16 is the expected plurality accuracy over random k-subsets (100 permutations, ties share credit), at tokens k × (mean tokens per pool sample). F is the isotonic (pool-adjacent-violators) fit, interpolated linearly in tokens; outside the pool's token range F is held at its end value and the result is flagged `beyond range`, where the gap is an upper bound on the true premium. `code/cme/frontier.py` implements this with known-answer tests.
**5.2 Inference.** Paired bootstrap over items, 2,000 resamples, seed 0, resampling the pool curve, the isotonic fit and the strategy accuracy together (percentile intervals). One-sided 95% limits for confirmatory tests; Holm correction across H1–H4 (family-wise α = 0.05) using bootstrap p-values from the resample distribution. H1 and H3 are tested as "gap ≤ 0" and "gap(S4) − gap(S3) = 0" respectively; failing to reject H1 does not establish that debate has no premium, and the report gives the interval.
**5.3 Secondary.** Interval of each strategy's gap in every cell; accuracy of each strategy against token cost on one axis; answer-change counts between round 1 and the final round (corrected vs corrupted); comparison S4 − S7 (messages versus extra context); S6 − S6v (diversity versus communication); S9 − S9i (feedback versus a verifier given to independent samples).
**5.4 Missing data and exclusions.** A response with no parsable answer or truncated at the cap is incorrect and counted (rate reported per strategy). Calls with missing token counts are flagged, never imputed.
**5.5 Sensitivity.** Exclude the 50 pilot items; completion-token frontier; a scorer using only the `Answer:` line; k = 8 pool.
**5.6 Exploratory.** Everything not listed, including heterogeneous-model analyses and cost-per-correct-answer, is labelled exploratory.

## 6. Other

**Deviations from the literature.** Local models (8–14B), plain MBPP in place of MBPP+, five agents and three rounds, plurality voting with tie sharing, and a synthetic positive control that is not a published benchmark.
**Known risks.** The hidden-profile control is solvable by a single agent given full evidence (greedy accuracy 0.92 for llama3.1:8b, 1.00 for qwen3:14b in the pilot), which is its design; its role is to show that the pipeline can detect a communication benefit when one exists. A null result on that task would indicate a pipeline or model problem.
**Author-owned decisions still open.** Whether to register before or after data collection, the primary-cell choice, δ, and whether MATH L4–5 (pilot greedy 0.36–0.38 for llama3.1:8b and qwen3:14b, near the lower end of the 40–75% headroom band) stays in the design.
