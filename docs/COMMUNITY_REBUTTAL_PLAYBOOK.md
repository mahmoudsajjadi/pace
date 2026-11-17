# Community rebuttal playbook: checking a multi-agent claim against its baselines

For reviewers, authors and readers who want to see how much of a reported multi-agent gain survives a stronger single-agent baseline. It contains a three-command check, drop-in review text, and the nine-column table that makes the comparison explicit. Everything runs offline from files; no model or network access is needed.

Setup (Python 3.9+, `numpy`, `matplotlib`):

```bash
cd code && export PYTHONPATH=.        # or: pip install -e code
```

## 1. The three-command review workflow

**Step 1: which rung is the baseline?** Describe the single-agent baseline the paper compares against in a JSON file and classify it.

```bash
echo '{"n_samples": 1}' > run_config.json
python -m cme classify --config run_config.json
# {"rung": "A", "rule": "R5", "reason": "single sample, no test-time scaling"}
```

Keys (all optional): `n_samples`, `aggregation` (`majority_vote`, `best_of_n`, ...), `extended_thinking`, `thinking_budget`, `search` (`mcts`, `tree`, ...), `matched_resource` (`thinking_tokens`, `total_tokens`, `cost`, `latency`, `iterations`, `generations`, `calls`, `flops`) with `matching_declared`, `n_budgets`, `pareto`. The five rules are in `code/mae_eval/classifier.py`: sweep or Pareto gives D; a declared matched resource gives C; extended thinking or search gives C (matching unverified); several independent samples combined by vote or selection gives B; anything else gives A. A configuration with inter-agent communication is rejected, because it is not a baseline.

**Step 2: what does sampling alone reach at the same tokens?** Given per-item sampled answers with token counts (`samples.jsonl`, the format written by `cme baseline`), draw the self-consistency frontier and, if you have the system's log, its points.

```bash
python -m cme frontier --samples samples.jsonl --logs logs.jsonl --out frontier.pdf
```

**Step 3: how far is the system from the frontier?**

```bash
python -m cme report --pool samples.jsonl --logs logs.jsonl --system debate --latex card.tex --json report.json
```

The output is the frontier gap (accuracy of the system minus the isotonic self-consistency frontier at the system's mean measured tokens) with a 95% paired bootstrap interval over items, the resource ratios (`n/a` when both sides are 0), and a LaTeX card. A positive interval that excludes zero means the system sits above what sampling reaches at that cost on those items; it does not identify why. The file schemas and a synthetic example are in `code/cme/README.md` and `code/cme/examples/`; the notebook `notebooks/cme_quickstart.ipynb` runs all steps on synthetic data.

If you only have the paper's tables, skip the three steps and transcribe the accuracies into a CSV for the nine-column table in section 2.

## 2. The nine-column audit table

```bash
python -m cme rebuttal --data ../outputs/baseline_tier_contrasts.csv --study Jwalapuram \
    --export-latex rebuttal_table.tex --export-markdown rebuttal_table.md
```

Without `--export-*` the table prints as Markdown; omit `--study` for all nine studies. `--data` is an alias of `--contrasts`. The bundled file is `outputs/baseline_tier_contrasts.csv` (832 rows: one per multi-agent configuration and baseline); `data/literature_contrasts.csv` does not exist, so point `--data` at the bundled file or at your own CSV (columns `study, category, baseline, key, d, cost_ratio, p_base, p_mas, n`; `category` is the rung and `key` is `Study|benchmark|model|configuration`; see `data/DATA_DICTIONARY.md`).

| Column | Meaning |
|---|---|
| Study, Benchmark, Model | where the contrast comes from |
| MA configuration | the multi-agent system or architecture arm |
| Baseline rung | A single greedy pass; B sampled baseline; C a named resource held equal or declared test-time scaling; D budget sweep |
| MA acc, Baseline acc | accuracies as extracted from the source table |
| Raw gap | MA acc minus Baseline acc for that row |
| Compute-normalized gap | MA acc minus the strongest single-agent baseline reported for the same configuration. It equals the raw gap on the row that already uses the strongest baseline and is lower on weaker-baseline rows. It is a within-study comparison, not a frontier estimate |

Cells a source does not report print `n/a`. Example (first rows of the Jwalapuram et al. contrasts in the bundled CSV):

| Study | Benchmark | Model | MA configuration | Baseline rung | MA acc | Baseline acc | Raw gap | Compute-normalized gap |
|---|---|---|---|---|---|---|---|---|
| Jwalapuram | GPQA-Diamond | GPT-4o | DyLAN | A | 0.530 | 0.534 | −0.004 | −0.016 |
| Jwalapuram | GPQA-Diamond | GPT-4o | DyLAN | B | 0.530 | 0.546 | −0.016 | −0.016 |
| Jwalapuram | GPQA-Diamond | GPT-4o | MAS-Zero | A | 0.434 | 0.534 | −0.100 | −0.112 |
| Jwalapuram | GPQA-Diamond | GPT-4o | MAS-Zero | B | 0.434 | 0.546 | −0.112 | −0.112 |

For DyLAN the gap against the single-pass baseline (rung A) is −0.004 and against the five-sample self-consistency row (rung B) is −0.016; the compute-normalized gap is the rung-B value on both rows because that baseline is stronger. For a single run of your own system, `cme report ... --export-markdown row.md --benchmark MMLU-Pro --model-label llama3.1:8b` writes a one-row table whose last column is the frontier gap with its bootstrap interval.

## 3. Review templates

Headings differ by venue and year; check the current review form and place the text where it asks for weaknesses, claims and evidence, or requested changes. Square brackets are for the reviewer to fill in. Keep the tone to the evidence: the templates ask for a comparison, they do not assume the result.

### Template A: claims built on a single-pass (rung A) baseline

> **Weakness (strength of the baseline).** The central claim, [quote the claim], is measured against [a single greedy pass / a single sample] (a rung A baseline: one call, no test-time scaling). A multi-agent system also uses more samples and more tokens than that baseline, so the reported gain of [X points] combines the effect of coordination with the effect of extra computation, and the experiments as described cannot separate them.
>
> **Requested analyses.** (1) A sampled baseline with as many independent samples as there are agents, combined by majority vote or best-of-k (rung B). (2) Accuracy against measured tokens (prompt plus completion) for the proposed system and for self-consistency at several k, so that the comparison is at equal cost, with the matched resource named (rung C) and an interval over items. (3) The token, call and latency cost of the proposed system. [(4) If the task gives every agent the same prompt, say why communication should help, or add a task where the evidence is partitioned across agents.]
>
> **Why it matters.** In a nine-study synthesis of published comparisons (this repository), contrasts against single-pass baselines average −0.032 over 358 contrasts, and contrasts against sampled baselines average −0.051 over 360 contrasts (unweighted means over contrasts that share baselines; one study contributes 180 contrasts, and the synthesis is descriptive). Whether the present result differs from that pattern is what the requested analyses would show. If the gain remains over the sampled baseline at equal tokens, the claim is much stronger; if not, it should be narrowed to what the evidence supports.

### Template B: requesting the nine-column audit table

> **Requested change (baseline audit).** Please add a table with one row per multi-agent configuration and baseline and these columns: Study, Benchmark, Model, MA configuration, Baseline rung (A single pass; B sampled; C a named resource held equal; D budget sweep), MA accuracy, Baseline accuracy, Raw gap, and Compute-normalized gap (the gap against the strongest single-agent baseline reported for the same configuration). Rungs that were not run should appear as `n/a`, so that readers can see which comparisons are missing. The table can be generated from a CSV with `cme rebuttal --data results.csv --export-latex table.tex` (a script and a classifier for the rungs are in the CME toolkit), and the baseline rung can be assigned with `cme classify`. Please also report the tokens used by each system, and whether prompt tokens served from a cache are counted.

### Venue wrappers (where to paste)

| Venue | Paste Template A under | Paste Template B under |
|---|---|---|
| NeurIPS | Weaknesses (then restate the requested analyses under Questions) | Questions |
| ICML | Claims and Evidence, or Experimental Designs or Analyses | Experimental Designs or Analyses |
| ICLR | Weaknesses (then Questions) | Questions |
| TMLR | the claims-and-evidence section, with the requested analyses as requested changes that are critical to acceptance | requested changes that would strengthen the work |

The wrapper table is a convenience: form fields change between years, and this repository does not hold copies of the venues' forms.

## 4. What the table and the commands do and do not show

- Rows within a study share baselines and are not independent; the table is descriptive and carries no standard errors. The bootstrap interval of `cme report` is over items of one run, not over studies.
- A negative compute-normalized gap says a stronger single-agent baseline was available in the same study. It does not say the multi-agent system could not win under a different matched budget.
- Rung C rows from extended thinking or search have unverified budget equality unless a matched resource is named; check the source before citing them as matched.
- Prompt-token counts from some servers omit tokens read from a cache, so token costs of strategies that repeat long prefixes can be understated.
- The bundled CSV was extracted with AI assistance and audited on a stratified sample (`review/AI_ASSISTED_EXTRACTION_AUDIT.md`). Check the source cell before relying on a contested row, and report mismatches.
