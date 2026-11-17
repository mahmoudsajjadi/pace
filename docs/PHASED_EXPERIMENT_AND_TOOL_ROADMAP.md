# Phased Experiment, Tooling, and Release Roadmap (Post-Commit `6f49f3d`)

> **Repository context note (added when archiving on 2026-11-11):**
> - **Current HEAD:** Commit `6f49f3d` (`refactor(manuscript): complete 10-item revision, CHE REML, visual/CLI updates, and TMLR polish`), extending `713c89c`.
> - **Verified baseline state:** `manuscript/tmlr_submission.pdf` (32 pages) and `manuscript/main.pdf` (36 pages) compile cleanly with zero LaTeX warnings; `pytest tests/ -v` runs 225 collected items (`224 passed, 1 skipped` — `test_load_gsm8k_test_sample_records_reproducible_provenance` skips when `pyarrow` is absent).
> - **Companion brief:** See `docs/CLAUDE_MASTER_BRIEF.md` for `AGENTS.md` manuscript style rules, TMLR double-blind constraints, owner-only/local-only Git policy, and prior literature notes. **Do not claim any external paper fact, abstract number check, or benchmark result was verified unless directly checked and evidenced.**
> - **Note on Title:** Unlike the earlier freeze note in `docs/CLAUDE_MASTER_BRIEF.md`, Section 1 below reopens the title wording and recommends deciding final wording after the controlled experiment completes.

---

Reaching the adoption scenario, and going 50% beyond it, depends on four things:
- an experiment that answers the question in your title;
- a tool that works with no code changes;
- data that saves other researchers compute;
- a benchmark where communication is guaranteed to help.

The plan below covers all four. First, a few problems in this build to fix before building on it.

## 0. Fix in this build first

1. **Nobody has hand-checked any extracted number.**
   - The paper now says, honestly, that AI tools did all extraction and checking and that you didn't inspect the sources by hand. For a paper built on extracted numbers, reviewers will treat that as the biggest weakness.
   - Spend 3–4 hours checking by hand every number in the abstract, all of Choi's and Wunderlich's values, and the 40 ledger rows. Then the paper can truthfully say you did.
   - Rename `HUMAN_VERIFICATION_AUDIT.md`. Its name currently contradicts the text.
2. **"Comparable-compute studies" in the abstract overstates.** Category B baselines are matched on samples, not compute. Say "sampled or budget-matched".
3. **Figure 4 has two rendering glitches:** "β̂β̂" prints twice, and "Δ_gap" appears as raw text.
4. **Three facts to verify against the sources:**
   - Wunderlich's "10-sample" self-consistency: check the sample count in their table.
   - Whether Wunderlich's mixture-of-agents (MoA) proposers were different models or copies of one. Table 9 calls them "cross-model".
   - Table 9's Zhang example (AGIEval +0.004) is an average over debate methods, not a result about using different models.
5. **Small fixes.**
   - Clipping and Haldane–Anscombe are still both described.
   - The command-line tool prints a ratio of 1 when both values are 0; it should print "n/a".
   - Label the bundled trace as a synthetic example.
6. **Figures.** Redraw Figure 1 as a vector graphic, and drop the archival Figure 10, which now repeats Figure 2.

## 1. Title

The current title says "Samples" and "Sampling", and "More Thinking" and "Test-Time Compute", which repeats two ideas. A good title keeps a memorable hook, contains the words people search for (debate, self-consistency, compute-matched, baselines), and stays under about 14 words.

| Option | When to use it |
|---|---|
| **More Agents, More Samples, or More Thinking? Compute-Matched Baselines for Multi-Agent LLMs** | Now (my recommendation). Keeps your hook, echoes "More Agents Is All You Need" so people searching for that find you, and adds the phrase reviewers will type. |
| More Agents, More Samples, or More Thinking? Debate Rarely Beats Self-Consistency at Matched Compute | After the experiment, only if it confirms the pattern. Answer titles get more attention, but must stay true. |
| Talk or Vote? Separating Communication from Sampling in Multi-Agent LLMs | A punchier alternative if you'd rather drop the current hook. |
| Is the Talking Worth the Tokens? Compute-Matched Evaluation of Multi-Agent LLMs | Same, with a cost angle. |

Decide the final wording after the experiment.

## 2. The experiment: run the race your title asks about

Your title poses a three-way race: more agents, more samples, or more thinking. No paper I know of runs all three head-to-head at matched tokens on the same items. Make that the centerpiece.

**Strategies, run on the same items with the same model.** Debate's first-round answers are reused as the voting samples, so debate and voting differ only by the messages.

| # | Strategy | What it tests |
|---|---|---|
| 1 | Greedy, one call | Category A baseline |
| 2 | Pool of 16 independent samples; self-consistency at k = 1 to 16 | "More samples", and the frontier curve |
| 3 | One call at higher reasoning effort or a larger thinking budget | "More thinking" |
| 4 | Vanilla debate, five copies of one model, two or three rounds | "More agents" |
| 5 | Debate with confidence-weighted aggregation | Breaks the uniform-update condition |
| 6 | Debate among different models, compared with voting by the same mix of models | Whether model diversity or communication drives any gain |
| 7 | Placebo debate: peer messages replaced by unrelated rationales of matched length | Meaningful messages versus extra context |
| 8 | An aggregator that writes a new answer (Wunderlich's mixture-of-agents) | Replicates the one positive result |
| 9 | Verifier condition: agents get unit-test feedback, and the independent agents get the same verifier | Separates a tool effect from communication |

**Tasks.** Include one where communication must help by construction.

| Task | Items | Purpose |
|---|---|---|
| MMLU-Pro subset | 1,000 | Replicates Wunderlich, the only positive result |
| Hard math (MATH-500 levels 4–5, or a recent set to limit contamination) | 500 | Sequential reasoning, where debate is expected to lose |
| MuSiQue 4-hop, full context | 500 | Replicates Tran and Kiela |
| **Positive control:** the same questions with the evidence split across agents, like the "hidden profile" tasks from group-decision research (Stasser and Titus, 1985) | 300–500 | Communication is needed here. If your method detects a premium on this task and none on the others, the method is validated. This is a strong credibility point. |
| Code with unit tests (MBPP+ or HumanEval+) | 300 | The verifier condition |

**Models people want to see.**

| Tier | Models | Why |
|---|---|---|
| Local, free and reproducible | Qwen3 14B (thinking on and off), DeepSeek-R1-Distill 14B, Llama 3.1 8B, Gemma 4 12B, OLMo 3 7B (fully open) | Anyone can rerun them. Drop granite-guardian, and keep qwen2.5-coder for the code task only. |
| Hosted open weights, free tier or cheap | gpt-oss-120b and gpt-oss-20b at low, medium and high reasoning effort; Qwen3.8 27B; DeepSeek V4.1 Flash | The reasoning-effort settings are exactly your "more thinking" condition. |
| Closed frontier models, on a 300-item subset | One cheap tier each from OpenAI, Anthropic and Google | Readers will ask whether the result holds at the frontier, and model names in your results get searched. |

**Statistics.**
- Preregister on OSF, which can give an anonymized view-only link for review.
- Hypotheses:
  - H1: vanilla homogeneous debate has a premium of zero or less.
  - H2: the positive-control task shows a premium above zero.
  - H3: the ordering of more agents, more samples and more thinking at matched tokens.
  - H4: Wunderlich replicates.
- **The estimand (the frontier gap):** a strategy's accuracy minus the self-consistency curve's accuracy at that strategy's measured token cost.
- Use paired bootstrap confidence intervals over items, and apply a Holm correction across the four hypotheses.
- With 1,000 items you can detect differences of about 3 points.

**Compute.**
- At about 50 calls per item, the local runs take overnight batches over about two weeks.
- Use Ollama's `OLLAMA_NUM_PARALLEL` or llama.cpp's parallel slots; local requests can run in parallel.
- Reuse first-round samples across strategies to cut the number of calls by about a third.
- Hosted runs cost roughly $100 per frontier model for 300 items at $2 in / $10 out per million tokens. Measure the real figure in a 50-item pilot before committing.

## 3. The tool: zero-friction for any researcher

Design it around three commands. The first is the adoption trick.

1. **`cme proxy`.** An OpenAI-compatible logging proxy. Point any agent framework's base URL at it, and every call's tokens, latency and cost are logged with no code changes. Build on LiteLLM's proxy instead of from scratch.
2. **`cme baseline --model X --bench Y`.** Generates the greedy run and the 16-sample pool with your prompts. It caches results and resumes if interrupted.
3. **`cme report --logs run.jsonl`.** Produces:
   - the self-consistency frontier;
   - the system's premium with a confidence interval;
   - the six-dimension resource card with warnings;
   - a LaTeX table and a figure ready for a paper.

**Supporting pieces.**
- **Python API:** three functions (`frontier`, `premium`, `resource_card`).
- **Adapters:**
  - OpenAI-compatible servers, which covers Ollama, vLLM, llama.cpp, Groq and OpenRouter;
  - Anthropic and Gemini;
  - importers for lm-evaluation-harness and Inspect logs.
- **Docs:**
  - a README whose first screen is a 60-second quickstart;
  - a Colab notebook;
  - a docs site;
  - support for Windows, Mac and Linux.
- **Engineering:**
  - tests against reference traces with known answers;
  - continuous integration;
  - versioned releases with Zenodo DOIs;
  - a `CITATION.cff` file whose preferred citation is the paper.
- **Licenses:** Apache-2.0 for code, CC BY 4.0 for data.

## 4. Data releases (each one gives people a reason to cite you)

| Release | Contents | Why people reuse it |
|---|---|---|
| Literature contrasts | The 531 rows with category labels, source page and table for each, and a data dictionary | Meta-analysis and checking related work |
| Self-consistency sample pools | 16 samples per item for every model and benchmark, with token counts | Anyone can compute a frontier for these models without paying for baselines |
| Full experiment logs | Every call, message and round | Studying debate dynamics and replication |
| Positive-control benchmark | The split-evidence task, with a name and a dataset card | Benchmarks are cited every time they're used |

Host them on Hugging Face Datasets with machine-readable metadata (Croissant), plus a Zenodo DOI.

## 5. A living leaderboard (maintained by automation)

- **Format:** a static GitHub Pages site or a Hugging Face Space.
- **Rows:** method × model × task.
- **Columns:**
  - premium against matched self-consistency;
  - tokens, cost and latency;
  - verification status.
- **Submissions:** pull requests that include logs. Continuous integration recomputes every number, so you don't verify by hand.
- **Rule:** never rank systems evaluated at different budgets against each other.
- **Upkeep:** re-run on new open models each quarter. Every model release brings new readers.

## 6. Figures

| Figure | Content | Why it gets shared |
|---|---|---|
| Opening figure (page 2) | Panel A: the waterfall, as it exists now. Panel B: the self-consistency curve with debate and other points from your experiment, so readers see whether the dot sits above the curve. | Explains the paper in five seconds |
| Baseline ladder | Your Figure 1, redrawn as a vector graphic | The vocabulary people will reuse |
| Forest plot | Each study's mean against Category A and against B/C, with intervals and the pooled estimate as a diamond | The plot meta-analysis reviewers expect |
| Cost-ratio scatter | All 516 configurations: accuracy difference against the multi-agent/single-agent call ratio on a log axis, colored by category | Shows that bigger budgets bought nothing |
| Frontier grid | Small panels for each model and benchmark: the self-consistency curve, the high-effort single call, and the debate variants | The main experimental result |
| Premium heatmap | Model × task, with the premium and its interval in each cell; the positive-control column should light up | When communication helps, at a glance |
| Answer-flow diagram | Across debate rounds: correct to wrong, wrong to correct, for vanilla, confidence-weighted and placebo debate | Shows debate corrupting correct answers |
| Resource card example | Real output from `cme report` | Shows the tool working |

**Design rules.**
- Use the colorblind-safe Okabe–Ito palette.
- Give each condition one fixed color across all figures.
- Export vector PDFs with fonts of at least 8 pt.
- Mark truncated axes. Figure 2 currently starts at 0.6 without saying so.

## 7. Restructure the paper

1. Introduction, ending with one quotable principle: a multi-agent gain should not be credited to communication unless it beats the self-consistency frontier at the measured cost.
2. Related work.
3. Framework: the baseline ladder, the frontier gap, and the waterfall.
4. Literature audit, condensed from your current Sections 5–6.
5. **The controlled experiment (new).**
6. Tool and reporting standard.
7. Discussion: when communication helps, built from Table 9 and the experiment's results.

Move to the appendix: the threshold analysis, the mechanism figure, and the REML details. The abstract should lead with the experiment's result, plus one literature number.

## 8. Launch

- **Release everything the same day:** paper, code, data, leaderboard and Colab. Check TMLR's FAQ on posting preprints during review first; until then, the supplementary zip covers reviewers.
- **Announce it:** a thread built on the opening figure, a short blog post, and submissions to agent and evaluation workshops.
- **Email the authors of the nine studies** with their extracted rows, and offer to compute their systems' premium. People cite work that includes them.
- **Offer integrations:** pull requests to lm-evaluation-harness and Inspect, and a "measure your system" guide for popular agent frameworks.
- **Find co-maintainers** for the leaderboard, so it outlives your own available time.

## 9. Timeline (aim for mid-January; submit only once the build checks pass)

| Dates | Work |
|---|---|
| Nov 11–17 | Fixes from section 0, your hand check, preregistration, tool skeleton (proxy, frontier, report), 50-item pilots |
| Nov 18 – Dec 8 | Main runs: local models overnight, hosted models in parallel |
| Dec 9–15 | Analysis and figures |
| Dec 16–29 | Rewrite; tool documentation, Colab and datasets |
| Dec 30 – Jan 15 | Full read-through, consistency checks, submission |

## 10. What this buys (my judgment)

The adoption scenario from before reached about 840 citations by 2035. Adding 50% means about 1,250. Beyond the core plan, the extra comes from four things:
- frontier-model results, because people search for model names;
- the positive-control benchmark, which gets cited every time it's used;
- quarterly leaderboard refreshes;
- integrations with existing evaluation tools.

All of this depends on other researchers actually using the tool and data, which you can't guarantee. Maintenance costs a few hours a month.

## Prompt for the coding agent

```text
Read docs/CLAUDE_MASTER_BRIEF.md, then this plan. After each task, show evidence
(command output, file paths, or lines from the compiled PDF text). Do not report
anything done without evidence. Local commits only.

Phase 0 (this build): fix "comparable-compute" wording, Figure 4 glyph errors,
clipping vs Haldane-Anscombe, CLI 0/0 ratio, label sample_trace.jsonl as
synthetic, vectorize Figure 1, remove Figure 10. List every number in the
abstract with its source table and page so I can check them by hand.

Phase 1 (tool skeleton): package cme with three commands:
- cme proxy: OpenAI-compatible logging proxy (build on LiteLLM) writing JSONL
  with per-call input/output/reasoning tokens, latency, cost, model, round.
- cme baseline: greedy + 16-sample pool, cached and resumable.
- cme report: isotonic self-consistency frontier vs measured tokens, frontier
  gap with paired bootstrap CI, six-dimension resource card with flags,
  LaTeX table, PNG/PDF figure.
Tests with reference traces; CI; README 60-second quickstart; Colab notebook.

Phase 2 (experiment harness): strategies 1-9 from the plan, sharing round-1
samples; tasks: MMLU-Pro 1,000, hard math 500, MuSiQue 4-hop 500,
split-evidence positive control 300-500, code with unit tests 300.
Temperature > 0 with distinct seeds for all sampled arms; record the model
digest for every local model. Run a 50-item pilot per model and report calls,
tokens, wall time and projected cost before any full run.

Phase 3 (analysis and figures): frontier grid, premium heatmap, answer-flow
diagram, forest plot, cost-ratio scatter, opening figure; Okabe-Ito palette,
vector output, all numbers via macros.

Phase 4 (release prep): Hugging Face dataset cards (literature contrasts,
sample pools, logs, positive-control task), CITATION.cff with the paper as
preferred citation, static leaderboard with CI recomputation from submitted
logs. Do not publish anything until I approve.
```
