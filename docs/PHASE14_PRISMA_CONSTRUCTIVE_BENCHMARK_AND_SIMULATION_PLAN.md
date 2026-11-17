# Phase 14: Constructive Benchmark Program, PRISMA 2020 Systematic Review, Estimator Simulations, and Long-Term Citation Roadmap

> **Scope & Author Override Note:**
> - **Page Count Constraint Suspended:** Per author directive (*"no page count at this point"*), the 12-page main-text ceiling is **not enforced** during this phase. Length trimming is deferred until content integration and empirical runs are complete.
> - **Honest Limits:** Target **75%–85%** single-submission acceptance at TMLR (**90%–95%** over a revise-and-resubmit cycle). Achieving >10,000 citations (~1% prior) requires obligatory benchmark and software adoption across frontier model cards; the program below maximizes the path toward 1,000–3,000+ citations.

---

## Core Strategic Insights

1. **TMLR Evaluates Correctness, Evidence, and Clarity:** Novelty claims carry less weight than ironclad evidence, explicit error bounds, zero overclaiming, and cohesive authorial voice.
2. **Negative Results Plateau; Constructive Diagnostics Compound:** Simply showing "debate fails to beat voting" saturates quickly. Lasting impact requires explaining *when* communication succeeds and providing the standardized diagnostic to prove it.
3. **Obligatory Use Drives Scale:** Only software integrations (`inspect_ai`, `lm-evaluation-harness`) and diagnostic benchmarks whose scores improve with model capability get embedded in frontier evaluation pipelines.

---

## Part A: Acceptance Program (From ~25% to ~80% Per Submission)

### A1. Constructive Repositioning
- **Core Argument:** When agents observe identical evidence, communication creates no new information, so gains come strictly from extra compute or aggregation. Communication succeeds when:
  1. Evidence is partitioned across agents (**Route I**);
  2. Outputs can be filtered or gated by an external verifier (**Route II**); or
  3. Diverse models commit distinct, decorrelated errors (**Route III**).
- **Candidate Title Option:** *More Agents, More Samples, or More Thinking? When Communication Helps Multi-Agent LLMs*.

### A2. Triangulated Evidence Matrix (Theory $\times$ Literature $\times$ Experiment)

| Prediction | Theory | Literature (Meta-Regression Moderator) | Experiment |
| :--- | :--- | :--- | :--- |
| **No premium when evidence is shared** | Proposition 3.1 ($\mathcal{I}=0$) | Studies where every agent sees the identical prompt | `MMLU-Pro` and `MATH-500` (hard) |
| **Premium when evidence is split** | Route I (Fano gap) | Partitioned-context / decomposable tasks | 2×2 Positive Control (Hidden Profile) |
| **Verifiers raise the premium** | Route II ($\tau_{c\to i} \to 0$) | Studies using compilers, unit tests, or domain verifiers | Code with unit tests (both arms get verifier) |
| **Different models decorrelate errors** | Route III & $K_{\mathrm{eff}}$ | Heterogeneous model runs (Zhang hetero, Ferreira) | Mixed-model debate vs. mixed-model voting |

### A3. PRISMA 2020 Systematic Review Protocol
1. **OSF Registration Before Searching:** Register questions, eligibility criteria, database list, exact search queries, date window, extraction schema, risk-of-bias rubric, and meta-regression/TOST plan using an anonymized view-only link.
2. **Multi-Database Search & Citation Chasing:** Query arXiv, Semantic Scholar, ACL Anthology, and OpenReview; run backward and forward citation chasing from the 9 seed studies.
3. **Dual Independent Screening & Extraction:** Two independent human raters screen titles/abstracts and full texts, and independently extract headline rows plus a blind 20% random audit, reporting Cohen's $\kappa$.
4. **Adapted Risk-of-Bias Rubric:** Score each paper on baseline strength & compute matching, item counts/seeds/contamination checks, and selective reporting (e.g., max-over-settings rows).
5. **Reporting & Equivalence Testing (TOST):** Include a PRISMA flow diagram and checklist comparing the 9-study seed set against the full corpus. Run meta-regression over A2 moderators plus **Two One-Sided Tests (TOST)** on the pooled effect to establish equivalence positively rather than inferring null effects from non-significance.

### A4. Confirmatory Experiment Upgrades
- **Preregistration:** Register H1–H4 alongside mechanistic predictions measured directly from logs (transition rates $\tau_{i\to c}, \tau_{c\to i}$, crossover threshold $\hat{p}^*$, peer error correlation $\rho_{\mathrm{peer}}$, quadratic token growth).
- **TOST Equivalence Margin & Power:** Pre-specify a $\pm 2$-point equivalence margin for H1; plan $N \approx 1,000$ items per benchmark to detect ~3-point differences.
- **Robustness Grid:** 3 prompt templates $\times$ 3 seeds $\times$ 2 temperatures on the primary contrast.
- **Full Control Suite:** Placebo messages, omniscient full-evidence single agent, independent voting over partitioned views, and the full self-consistency curve.
- **Model Tiers & External Validity:** 3 local open models, 2 hosted open-weight models, and 2–3 frontier models on a subset, plus a tool-using coding task with unit tests. Release every raw log.

### A5. Monte Carlo Estimator Validation (Simulation Study)
- Generate synthetic accuracy-vs-token scaling curves with planted ground-truth gaps.
- Verify that the frontier-gap estimator is unbiased and its 95% bootstrap intervals achieve nominal coverage at experimental sample sizes.
- Validate CR2 small-sample interval coverage across 8–20 study clusters under varying intra-cluster correlations.

### A6. Editorial & Claims Discipline
- **No Page Count Cap Enforced Now:** Length ceiling (e.g., $\le 12$ pages) is suspended at this stage.
- **Eliminate Numeric Echoes:** Restrict each key statistic to appear at most twice across the main text (avoiding verbatim repeats across Abstract, Contributions, §5.3, §7.1, Conclusion, and Tables).
- **Claims Ledger:** Map every claim in the Abstract, Introduction, and Conclusion directly to its supporting table or figure; delete any unsupported claim.
- **Authorial Voice & Terminology:** Author rewrites Abstract, Introduction, and Discussion in natural human prose; standardize one term per concept globally.

### A7–A10. Submission & Review Readiness
- **Desk-Rejection Guard:** Official TMLR anonymized style, mandatory Page-1 AI-use footnote, zero identifying links, working supplementary zip, grayscale-safe figures, zero LaTeX warnings/placeholders.
- **Human Team:** Recruit second screener/extractor, UNR statistician review, and 3 pre-submission readers (MAS researcher, meta-science statistician, generalist).
- **Defense Readiness:** Prepare table/figure defense notes, hand-verify every proof step, conduct mock author Q&A, nominate 3 evaluation/meta-science Action Editors.

---

## Part B: Long-Term Citation & Benchmark Ecosystem Program

### Six Reinforcing Outputs
1. **Paper 1 (TMLR, Spring 2027):** Establishes the compute-matched protocol, meta-analysis, and theoretical bounds.
2. **Separate Benchmark Paper (Datasets & Benchmarks Track, 2027):**
   - Procedural, contamination-resistant generator with private test seeds and configurable difficulty (agents, partitions, distractors, depth).
   - Paired **shared-evidence vs. split-evidence twins** on every item so coordination necessity is tested cleanly.
   - Five natural-language domains: hidden-profile decisions, split-document multihop QA, distributed constraint scheduling, split-codebase debugging with unit tests, and private-information cooperative games.
   - Automatic deterministic scoring plus a cheap 200-item `"lite"` split designed for frontier model cards.
3. **Ecosystem Integrations:** Official adapters in `inspect_ai` and `lm-evaluation-harness`, plus a public leaderboard featuring token/cost parity columns.
4. **Annual Living Audit ("State of Multi-Agent Evaluation", Late 2027+):** Longitudinal tracking report quoted in subsequent literature introductions.
5. **Workshop Shared Task (2028):** Community competition centered on partitioned multi-agent coordination.
6. **Author Consortium Re-Analysis (2027–2028):** Item-level log pooled meta-analysis with primary source authors.

---

## Part C: 12-Month Execution Schedule (20–25 hrs/week; ~$200–$1,000 API Budget)

- **Nov 12–30:** Immediate compliance fixes, author hand-check & proof walkthrough, recruit second rater & statistician, register OSF review & experiment protocols.
- **December:** Literature search & dual screening; run 2×2 positive control across 3 models; launch main confirmatory runs.
- **January:** Dual extraction & risk-of-bias scoring; finish main experiments, simulation study, and meta-regression/TOST.
- **February:** Author rewrite in personal voice; claims ledger audit; two weeks of external reader review.
- **Early March:** TMLR submission, arXiv preprint, public code/data/tool release, Chinese-language summary, teaching kit.
- **March–May:** Benchmark v1 (2–3 domains), Inspect/lm-eval PRs, frontier baselines, Datasets & Benchmarks submission.
- **Summer–Fall:** TMLR revisions, workshop shared-task proposal, first annual audit report.

---

## Part D: Immediate Developer Directives (Excluding Page Limit)

1. **OSF Review Protocol Draft:** Draft formal OSF protocol (`docs/PREREGISTRATION_PRISMA_REVIEW.md`) specifying questions, eligibility rules, 4 databases, search strings, date window, extraction schema, risk-of-bias rubric, moderator meta-regression, and TOST margins. Wait for `[ME]` approval before running the formal search.
2. **PRISMA Search & Blind Screening Pipeline:** Script queries across arXiv, Semantic Scholar, ACL Anthology, OpenReview + backward/forward citation chasing from the 9 seed studies; save raw results, deduplicate, and export blind dual-rater screening sheets + Cohen's $\kappa$ script (never autofill rater decisions).
3. **Dual Extraction & Risk-of-Bias Tooling:** Generate dual-extraction templates, agreement scripts, risk-of-bias table builder, and PRISMA flow diagram generator.
4. **Moderator Meta-Regression & TOST:** Implement meta-regression (shared vs. split evidence, verifier present, heterogeneous models, baseline category) with CR2 intervals and TOST equivalence test on the pooled effect, comparing seed set vs. full set.
5. **Simulation Study (`scripts/run_estimator_simulations.py`):** Implement synthetic Monte Carlo verification checking bias and 95% CI coverage for both the frontier-gap estimator and CR2 cluster intervals across 8–20 clusters.
6. **Claims Ledger Audit (`review/CLAIMS_LEDGER.csv`):** Build script/table mapping every claim in Abstract, Introduction, and Conclusion to its backing table/figure/equation, flagging unsupported claims and flagging numbers repeated >2 times in main text.
7. **Separate Benchmark Package Scaffold (`benchmarks/split_coord_bench/`):** Scaffold the 5 natural-language domain generators with shared/split twins, private-seed procedural generation, lite split (`N=200`), and adapters for `inspect_ai` and `lm-evaluation-harness`.
