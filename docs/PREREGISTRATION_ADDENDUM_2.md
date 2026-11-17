# Addendum 2 to the experiment protocol (2026-11-12): a defect in split-evidence debate, and three exploratory experiments

Status: not registered. It follows `docs/PREREGISTRATION.md` and `docs/PREREGISTRATION_ADDENDUM_1.md`. No outcome of any confirmatory cell has been analysed; only counts of finished items were read.

## 1. Defect found in debate on split evidence

**What.** `cme.experiment._debate` built the prompt of every debate round from `item["prompt"]`. For items with split evidence (`views`), `item["prompt"]` is the full-evidence prompt. Round 1 correctly used one view per agent, but in rounds 2 and later every agent was shown all of the evidence. Debate on the hidden-profile task therefore gave each agent the pooled evidence from round 2 on, which is not the split-evidence design of H2.

**Evidence.** A probe with a recording client on one hidden-profile item (`tests/test_split_debate_views.py` reproduces the fixed behaviour) printed 24 criterion lines in each round-1 prompt (4 shared plus 2 split criteria, four candidates) and 40 criterion lines in each round-2 prompt (all ten criteria) before the fix, and 24 in every round after it.

**Affected data.** The llama3.1:8b hidden-profile cell `outputs/experiments/confirmatory/llama3.1-8b__hidden_profile` contains results labelled `S4` (196 of 200 items finished when this was found) produced by the defective implementation. They are kept unchanged and are not to be used as the H2 debate arm. Not affected: `S1`, `S2`, `S2v` and every MMLU-Pro strategy (no views). The later hidden-profile strategies `S5` and `S7` had not started and will run with the fix.

**Fix (2026-11-12).** `_debate` now shows an agent only its own view in every round. Debate on items with views is strategy `S4v` with its own label and its own call keys (`S4v|...`), so results of the defective implementation are neither reused nor skipped. `analysis/make_confirmatory_numbers.py` takes H2 from `S4v`. The processes that were already running keep the old code until they finish; every process started afterwards uses the fix. A rerun of `S4v` on the 200 hidden-profile items reuses the round-1 view calls of `S2v` (same keys) and needs about 2,000 new calls; it is queued behind the running batch (`scripts/queue_phase16.sh`).

**Consequence for H2.** H2 is evaluated on `S4v`. The leaked `S4` arm may be reported, labelled as debate in which agents receive the full evidence after round 1, as a descriptive contrast; it is not a test of the preregistered hypothesis.

## 2. Exploratory experiments (not confirmatory, not part of H1 to H4)

All use local Ollama models, temperature 0.7 for sampled calls, greedy for S1, seeds from the harness (`--seed 0`), and are run only after the running batch has finished. Results are reported as descriptive, with item-bootstrap intervals, and labelled exploratory.

- **Experiment 2: Stasser and Titus 2x2 on the hidden-profile task.** First 100 items of the seed-42 task (the same items as the released file), llama3.1:8b, 5 agents. Evidence: split (each agent sees its view) versus shared (each agent sees all evidence). Mechanism: independent voting over 5 agents (one round) versus debate for 2 rounds. Cells: split voting `S2v`, split debate `S4v`, shared voting `S2` with k = 5, shared debate `S4`. Estimand: debate minus voting within each evidence condition and their difference.
- **Experiment 3a (Route II): verifier-gated debate.** GSM8K, 100 items, llama3.1:8b, 5 agents, 3 rounds. Each response must give an arithmetic expression and an answer. A deterministic evaluator (`cme.verifier`, a restricted arithmetic parser, no code execution) checks that the expression evaluates to the stated answer; an agent's changed answer is accepted only if it passes. It checks the calculation, not the reading of the problem, so it is a partial verifier. Compared with ungated debate on the same items (`S4`).
- **Experiment 1: debate dynamics.** GSM8K (100 items) and MATH levels 4 to 5 (100 items), llama3.1:8b and one further installed non-reasoning model, arms greedy (S1), 5-sample vote (S2 with k = 5), more thinking (S3), debate with 5 agents and 3 rounds (S4). Measurements by `cme dynamics`.
- **Experiment 3b (Route III): cross-model panel.** Not configured for the models named in the plan (Qwen2.5-7B-Instruct, Mistral-7B, Gemma-2-9B), because they are not installed and fetching them needs the author's approval. The configuration is written with those models marked not installed.
- GPQA-Diamond is gated on the Hugging Face hub and is not used.

## 3. What this addendum does not change
The confirmatory plan, the hypotheses H1 to H4 and their thresholds, and the running batch are unchanged. Nothing here is a result.
