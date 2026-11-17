# Phase 17: ArXiv Preprint Readiness, Critical Statistical & Baseline Corrections, and Two-Stage Publication Roadmap

> **Strategic Principle:** Freeze the exact title everywhere. Correct the statistical framing, baseline eligibility (Jwalapuram & Smit), and $N=100$ placeholder exclusions before posting v1 to arXiv. Position `cme` as permanent research infrastructure for compute-matched evaluation.

---

## 1. Frozen Title & ArXiv Formatting Rules

- **Exact Frozen Title (Do Not Alter):**
  > **More Agents, More Samples, or More Thinking? Untangling Coordination, Ensembling, and Test-Time Compute in Multi-Agent LLMs**
- **ArXiv Preprint vs. TMLR Submission Formatting:**
  - **ArXiv Preprint:** Use `\usepackage[preprint]{tmlr}` (per TMLR official FAQ recommendation), include full author name and UNR affiliation, **remove the `*` footnote marker from the title**, and place the AI-assistance and author-responsibility disclosure in its own dedicated section. Choose primary category `cs.CL` (with `cs.AI` cross-list as appropriate).
  - **TMLR Double-Blind Submission:** Keep `\usepackage{tmlr}` (anonymous mode) and retain the Page-1 AI-use footnote required by TMLR FAQ.

---

## 2. Critical & Major Fixes Required Before ArXiv v1 Upload

### Critical Fixes
1. **Statistical Interpretation (Remove Combined B/C REML from Abstract Headline):**
   - Do NOT present the combined B/C REML pooled estimate ($\hat{\beta} = -0.195$, 95% CI $[-0.320, -0.070]$) as the primary headline finding in the Abstract.
   - Categories B and C control different resources; only 8 studies enter the combined model with high heterogeneity ($I^2 \approx 93\%$), assumed $\varphi$, and upper CI crossing zero ($+0.002, +0.053$) under whole-study correlations $0.50$ and $0.80$.
   - **Action:** Make descriptive summaries primary in the Abstract and Main Text; keep REML explicitly framed as exploratory in the appendix (or heavily qualified).
2. **Baseline Eligibility (Jwalapuram Upper-Bound & Smit Median):**
   - Jwalapuram's 5-sample self-consistency row reports the *best observed* single-agent scores across multi-agent entries rather than conventional paired baselines.
   - **Action:** Reclassify Jwalapuram's 5-sample row as a **best-observed upper-bound reference**, exclude it from the primary Category B sample-matched summary, and report it in a separate sensitivity analysis. Also audit Smit et al.'s median-over-configurations before classifying as directly paired.
3. **Invented Sample-Size Placeholder (AGIEval $N=100$):**
   - Exclude any contrast using an invented `N=100` placeholder (where true evaluated $N$ is unreported) from all sample-size-dependent inferential models. Retain accuracy comparisons only in descriptive summaries with $N$ marked as unknown.

### Major & Important Corrections
4. **Separate Category B & C in Abstract & Keywords:**
   - Report Category A, Category B (sample-matched), and Category C (named-resource-matched) means separately rather than portraying B+C as one compute-matched estimand.
   - Remove `"Meta-Analysis"` from Keywords and title phrasing; replace with `"quantitative evidence synthesis"` and keywords: *Multi-Agent Systems, Test-Time Compute, Self-Consistency, Ensembling, Resource Accounting, Evaluation Methodology*.
5. **Evidence Selection & Extraction Transparency:**
   - Clearly describe the corpus as purposively selected (5 initial studies + 7 screened candidates), never retroactively claiming a comprehensive systematic search until the PRISMA search completes.
   - For the gold-standard journal version, independently verify every row of all 516 configurations in a source-linked extraction ledger (paper, table, page, row, column, value, classification, verification status).
6. **Clarify 6D Resource Vector Definitions (Prevent Double Counting):**
   - Clarify $R_{\mathrm{token}}$ vs. $R_{\mathrm{sys}}$ so scaffolding and tool-call tokens are not double-counted.
   - Explicitly distinguish end-to-end wall-clock execution time from the sum of per-call latencies in $R_{\mathrm{lat}}$.
7. **Other Targeted Adjustments:**
   - Show study-equal and contrast-weighted Category A summaries side by side (to show sensitivity to Zhang et al.).
   - Label Category D (2 Pareto-front comparisons) as illustrative/preliminary.
   - Move textbook Dec-POMDP/DPI/Markov derivations and fitted threshold illustrations to the appendix; keep only the core conceptual framework in main text.
   - Do not imply a universal empirical 45% threshold (since segmented regression shows no general break).

---

## 3. Literature Additions: 2026 Positive-Result Directions

Screen and integrate three recent 2026 positive-result studies in Related Work alongside a structured positive-return conditions table:
1. *Test-Time Compute Scales Better with Parallel Agent Teams* (Nov 6, 2026) — parallel teams of 10 outperforming independent agents on 10/12 long-horizon tasks.
2. *Scaling Discovery through Test-Time Communication* (Sept 17, 2026) — communication gains when progress feedback is present.
3. *Scaling Inference-Time Compute with Teams of Coding Agents* (Oct 12, 2026) — compute allocation across planning, implementation, and verification (3–7× cost).

**Positive-Return Table Dimensions:** Parallel sub-teams, Progress/verifier feedback, Partitioned evidence, Cross-model error diversity, Specialized tools, Task decomposability.

---

## 4. Two-Stage Publication & Infrastructure Strategy

### Stage 1: ArXiv v1 Pre-Upload Priority Checklist
1. Freeze exact title; remove `*` footnote from title and place disclosure in dedicated section; switch arXiv preprint to `\usepackage[preprint]{tmlr}`.
2. Fix bibliography identifiers and add the 2026 positive-result studies.
3. Adopt conservative Abstract separating Category B & C and removing pooled REML headline.
4. Reclassify Jwalapuram's best-observed baseline and audit Smit et al.
5. Exclude AGIEval `N=100` placeholder from inferential weighting.
6. Replace `"Meta-Analysis"` keyword.
7. Clarify purposive study selection and extraction status.
8. Fix $R_{\mathrm{token}}$/$R_{\mathrm{sys}}$ double-counting and wall-time vs. call-sum latency.
9. Build and verify clean arXiv source archive (`cs.CL` primary, `cs.AI` cross-list).
10. Verify all headline extracted values against primary sources.

### Stage 2: Long-Term CME Research Infrastructure
- **Executable Evaluation Standard:** `cme audit`, `cme compare`, `cme report --format html` outputting machine-readable JSON evaluation cards + HTML/PDF audit reports enforcing resource-matching rules without silently upgrading sample matching to token matching.
- **Comparison Registry & Immutable Leaderboard:** Source-linked ledger + versioned performance-vs-resource registry.
- **Rollout Cards Interoperability:** Actually run and validate the CME compute block against the Rollout Cards validator.
- **Original Controlled Experiment & External Replication:** Deliberately test both failure and success regimes (shared vs. partitioned evidence, with/without external verifiers, parallel vs. sequential, homogeneous vs. heterogeneous, short vs. long budgets) and invite 2–3 external groups to test usability.

---

## 5. 12-Item Pre-Submission Readiness Gate (TMLR)

1. All central numerical claims verified against primary sources.
2. No invented or placeholder sample sizes in inferential models.
3. Sample-matched (B) and named-resource-matched (C) comparisons separated.
4. Pooled REML model appropriately qualified / exploratory.
5. No claim of systematic search without documented PRISMA protocol.
6. Positive and negative 2026 literature fairly represented.
7. All 6 resource-vector dimensions operationally defined without double counting.
8. Source package compiles cleanly from scratch.
9. CLI passes clean-install and full test-suite checks.
10. Software and supplementary archives match manuscript statements.
11. Title, metadata, author info, and AI disclosure consistent.
12. Limitations accurately state what the evidence cannot establish.
