# Master Revision Plan: Multi-Agent Evaluation & Test-Time Scaling Standard
**Target Venues:** Nature Machine Intelligence / Leading AI Conferences (NeurIPS / ICML / ICLR)  
**Objective:** Transform Paper 01 into the definitive, field-wide evaluation standard (CME Standard & Multi-Agent Evaluation Observatory) capable of driving 10,000+ citations over 4–5 years.

---

## 1. Executive Summary & Reviewer Diagnosis

A critical senior reviewer audit evaluated the manuscript against the latest literature through November 2026. The verdict established that while the core question is of paramount importance, several scientific, empirical, and conceptual flaws must be resolved:
1. **Kim et al. (2026) Published in Nature Machine Intelligence:** Citing the 2025 arXiv preprint missed that Kim et al. expanded to 260 configurations, 6 benchmarks, 5 architectures, and 3 model families in *Nature Machine Intelligence* (July 24, 2026; DOI: `10.1038/s42256-026-01268-y`).
2. **Jwalapuram et al. Baseline Distortion & SMFR:** The manuscript compared MAS against a weak greedy CoT baseline rather than CoT with 5-sample Self-Consistency (CoT-SC), and incorrectly excluded SMFR ($N=588$ test samples, Appendix Table 6). Against CoT-SC, the multi-agent penalty deepens from $-0.018$ to $-0.045$, erasing all gains on GPQA and HLE-Maths.
3. **Incoherence of 5 CME Regimes:** The previous taxonomy mixed experimental controls (thinking tokens) with reporting formats (Pareto frontiers), contained untested regimes (Cost Matched was empty), and conflated agent count with sample count.
4. **Statistical Overreach:** Fitting a 3-level REML model with an assumed $\phi=0.50$ across 2–4 paper clusters produced degenerate cluster-robust degrees of freedom ($\nu \in [1.0, 2.0]$).
5. **Aesthetic & Reproducibility Gaps:** Lack of a public repository release, anonymous placeholders (`Research Team`), and overlapping figure panels.

---

## 2. Strategic Pivot: The 10,000-Citation Architecture

To achieve sustained, massive citations (comparable to ImageNet, GLUE, BLEU, HELM, or Kaplan et al. scaling laws), the paper will transition from a retrospective survey into **The Multi-Agent Evaluation Observatory (MAEO)**:

```
+---------------------------------------------------------------------------------------+
|                       MULTI-AGENT EVALUATION OBSERVATORY (MAEO)                        |
+---------------------------------------------------------------------------------------+
|  1. THE CME STANDARD & CHECKLIST       |  2. THE BENCHMARK OBSERVATORY LEADERBOARD    |
|  - 6-D Resource Accounting Vector      |  - Live interactive web dashboard            |
|  - Mandatory Reviewer Rubric for       |  - Tracks every MAS paper vs SAS compute     |
|    NeurIPS / ICML / ICLR / Nature MI   |  - Automated Pareto frontier generation      |
+----------------------------------------+----------------------------------------------+
|  3. OPEN EVALUATION SUITE (`mae-eval`) |  4. PERMANENT VERIFIED DATA REPOSITORY       |
|  - Pip-installable Python package      |  - Item-level & config-level open database   |
|  - Automates token, cost, latency audit|  - Permanent Zenodo DOI + versioned schemas  |
+---------------------------------------------------------------------------------------+
```

1. **The 6-Point Reviewer Checklist:** Embedded into conference review guidelines. Any submission claiming multi-agent superiority must report compute-matched baselines under the CME vector.
2. **Pip-Installable Audit Suite (`mae-eval`):** A drop-in evaluation library that logs reasoning tokens, scaffold overhead, API cost, and concurrency latency.
3. **Open Evidence Repository:** Machine-readable datasets archived on Zenodo with immutable DOIs and data dictionaries.

---

## 3. The 6-Dimensional Resource-Accounting Vector

Replace the 5 CME regimes with the formal resource-accounting vector:
$$\mathbf{R} = \langle R_{\text{reason}}, R_{\text{token}}, R_{\text{cost}}, R_{\text{lat}}, R_{\text{sample}}, R_{\text{sys}} \rangle$$

For any empirical comparison between MAS and SAS, each dimension must be classified:
- **Strictly Controlled:** Identical resource budget enforced (e.g., Tran & Kiela thinking tokens).
- **Approximately Matched:** Controlled within specified bounds (e.g., Kim et al. maximum iterations).
- **Unmatched (Measured):** Disclosed and audited, but unequal (e.g., Jwalapuram dollar costs).
- **Unreported:** Resource consumption omitted from the study.

---

## 4. Re-Analyzed Empirical Evidence Base

### Jwalapuram et al. Dual Baseline Audit (104 Contrasts with SMFR)
* **MAS vs Vanilla CoT ($m=104$):**
  * Overall Mean Difference: $\bar\Delta = -0.015$ (Cost ratio: $26.8\times$)
  * BrowseComp-Plus: $-0.0552$
  * GPQA-Diamond: $+0.0100$
  * HLE-Maths: $+0.0254$
  * SWE-Bench Lite: $-0.0641$
  * SMFR: $+0.0062$
* **MAS vs CoT-SC (5 samples; $m=104$):**
  * Overall Mean Difference: $\bar\Delta = \mathbf{-0.0465}$ (Cost ratio: $4.53\times$)
  * BrowseComp-Plus: $\mathbf{-0.0770}$
  * GPQA-Diamond: $\mathbf{-0.0094}$ (flips negative)
  * HLE-Maths: $\mathbf{-0.0004}$ (flips negative)
  * SWE-Bench Lite: $\mathbf{-0.1112}$ (severe collapse)
  * SMFR: $\mathbf{-0.0527}$ (severe collapse)
* **The "Expert MAS" Anomaly:** GPT-5 Expert MAS on SMFR achieved **96.51%** (vs CoT-SC 56.97%), demonstrating that only bespoke, human-engineered domain tooling—not automated conversational prompting—enables multi-agent breakthroughs.

### Kim et al. (Nature Machine Intelligence 2026) De-biasing
* All 4 architectures (Centralized, Decentralized, Hybrid, Independent) exhibit capability saturation above $\sim 45\%$ baseline accuracy on agentic code tasks.
* In contrast, Tran & Kiela's thinking-token matched QA benchmarks exhibit **no threshold**: single agents match or outperform debate across all budgets from 500 tokens upward, proving that Kim's threshold is task-structure dependent (decomposable tools vs multi-hop reasoning), not a universal law of coordination.

---

## 5. Statistical Synthesis Protocol

1. **Drop Inferential Meta-Analysis:** Discontinue the 3-level REML model and arbitrary $\phi=0.50$ assumption due to degenerate degrees of freedom ($\nu \le 2.0$).
2. **Three-Tier Descriptive Synthesis:**
   - Level 1: Configuration-level contrasts ($m=249$ verified pairs).
   - Level 2: Benchmark-level aggregated distributions.
   - Level 3: Study-level paradigm syntheses.
3. **Sensitivity Analysis Suite:**
   - Equal-study-weighted vs Equal-benchmark-weighted means.
   - Non-parametric Median and Interquartile Range (IQR).
   - Leave-One-Study-Out (LOO) influence checks.
   - Dual-baseline sensitivity (CoT vs CoT-SC).

---

## 6. Publication Figure Suite Architecture

* **Figure 1 (Page 2 Teaser):** The Three Confounders of Multi-Agent Evaluation
  - Panel A: Ensembling Confound (Choi voting vs debate).
  - Panel B: Compute Parity Reality (Tran token budget scaling).
  - Panel C: Baseline Distortion (Jwalapuram CoT vs CoT-SC penalty).
* **Figure 2:** Multi-Resource Evaluation Matrix & Evidence Gap Map (6D accounting across all studies).
* **Figure 3:** Thinking-Token Scaling Trajectories (Tran & Kiela disaggregated by FRAMES and MuSiQue).
* **Figure 4:** Accuracy-Cost-Latency Pareto Frontiers (MMLU-Pro, GPQA-Diamond, SWE-bench).
* **Figure 5:** Taxonomy of Agent Coordination Failures (Context dilution, duplicated tokens, error cascading, latency tax).
* **Figure 6:** Decision Framework: "When Should You Use Multiple Agents?" (Practitioner decision tree).

---

## 7. Execution Timeline & Milestones

1. **Milestone 1:** Re-extract Jwalapuram CoT-SC and SMFR data; update `evidence/` master CSVs.
2. **Milestone 2:** Update bibliography with Kim et al. *Nature Machine Intelligence* (2026) and 2026 additions.
3. **Milestone 3:** Replace Section 4 CME regimes with the 6D Resource Vector and update Section 5 with multi-tiered descriptive synthesis.
4. **Milestone 4:** Generate publication-grade figure pipeline (`analysis/plot_final_verified_figures.py`).
5. **Milestone 5:** Reassemble and compile `manuscript/main.tex` (solo-author metadata, zero placeholders).
6. **Milestone 6:** Generate open-source observatory documentation (`docs/CME_REVIEWER_CHECKLIST.md` and `docs/MAEO_SPECIFICATION.md`).

---

## Change log: 2026-11-09 session (mae-eval, dashboard, manuscript audit)

**Added**
- `code/mae_eval/` (`vector.py`, `tracker.py`, `auditor.py`, `__init__.py`): ResourceVector, ResourceTracker (call tracing, scaffold %, concurrency-aware latency, cost from user-registered prices), EvaluationAuditor (ratios, four control states, confounder flags, parity assertion). No provider price table is bundled on purpose (prices cannot be verified offline).
- `tests/test_mae_eval.py`: 11 tests on synthetic debate traces. Full suite: 168 passed (157 existing + 11).
- `analysis/export_maeo_json.py` -> `outputs/maeo_dashboard/{data.json,data.js}`; `outputs/maeo_dashboard/index.html` (filters, greedy-vs-CoT-SC toggle, Pareto chart, resource-vector radar/heatmap). Checked in headless Edge: 252 rows render; mean difference -0.0012 over all contrasts. CDN charts (Chart.js 4.4.1, Tailwind) not verified offline. The 6D control-state matrix is author-coded, not verified against the papers.

**Manuscript corrections (applied to the module files, which `analysis/assemble_paper.py` uses as source of truth; edits made directly to `main.tex` are overwritten on assembly)**
- CR2 intervals for Models A' and B were reported as "wide and conservative" but the table values were narrow ([-0.070,-0.006] at nu=2.1; [+0.262,+0.452] at nu=1.0). Leave-one-paper-out refits change the CR2 standard error of the pooled effect from 0.008 to 0.002, 0.043, or 0.066 while the model-based SE stays 0.027-0.066. CR2 is therefore not interpreted with 2-4 papers; text, abstract, conclusion and table caption updated. Leave-one-paper-out: Model B gap stays +0.352 to +0.373; Model A' moves -0.032 to -0.065.
- Softened over-claims: "confirms" -> "consistent with" (ensembling), "eliminates all multi-agent advantages" -> lowers the mean difference from -0.007 to -0.041, "demonstrating that breakthroughs require bespoke tooling" (one benchmark, one human-designed system), unverified mechanism ("duplicated tool calls"), unverified "ground-truth checks" in Expert MAS, "artifact of prompt formatting" (100-token result), conclusion claims about frontier models and deductive benchmarks.
- Removed markdown leakage (`**bold**`, backticks) from LaTeX; added narrative references for fig:three_faces, fig:resource_matrix, fig:pareto_frontier, fig:coordination_taxonomy, fig:decision_flowchart; fixed stale text in the theory section that said no pooled model existed; Limitations (ii) updated; novelty claim in related work now hedged.
- Overfull hboxes removed (`\emergencystretch` in the assembler preamble; one inline vector replaced by an equation reference; file names set with `\path`).

**Verified this session:** SMFR test N=588 (Jwalapuram App. Table 6); CoT-SC baseline = 5-sample majority vote (Jwalapuram Sec. 3.1); greedy mean -0.0071, CoT-SC mean -0.0405 over 107 contrasts (recomputed from `contrasts_dual_baseline.csv`); DOI 10.1038/s42256-026-01268-y exists in Crossref (Nature Machine Intelligence, 2026, Kim et al.) with the title "Capable language models can outgrow the benefits of collaboration".

**Open (needs the author):** see session report - author identity/contact, repository URL, Kim bibliographic record (title/version), OSF registration status, Kim NMI date/volume/pages, Expert MAS definition, 6D matrix coding.

---

## Change log: 2026-11-09 (second session): multi-tier synthesis, 2026 literature anchors, mae-eval packaging

**Author and venue facts supplied by the author:** sole author Seyed Mahmoud Sajjadi Mohammadabadi (mahmoud.sajjadi@unr.edu), repository URL as in `module5_open_science.tex` (stated as "will be made public").

**Added / changed**
- `analysis/run_multitier_synthesis.py` -> `manuscript/tables/table2_sensitivity_matrix.tex` (three tables: tiers L1/L2/L3, leave-one-study-out, dual-baseline by benchmark) and `outputs/multitier_synthesis.json`; integrated as Sec. 5.2 in `module2_empirical_overhaul.tex`. Key numbers: L1 mean -0.001 (median -0.006, IQR -0.044..+0.042); equal-cell +0.020; equal-study +0.013; dropping Choi -> +0.000; Choi-minus-others gap +0.046..+0.079 when Choi present; dual baseline -0.007 -> -0.041.
- Related work and discussion: MAS-Orchestra/MASBENCH (Ke et al., ICML 2026, arXiv:2601.14652), MASBench partial observability (Chu et al., arXiv:2610.04672), Nageshwaran et al. (Artif. Intell. Rev., 2026, DOI 10.1007/s10462-026-11678-4). Claims limited to what was read in the PDFs/Crossref record.
- Bibliography: Kim et al. now cites the published NMI record with Crossref volume/issue/pages (8(7), 1157-1172; the earlier 724-736 did not match Crossref); removed three earlier entries with unverified fields (wrong MASBench first author, invented volume/pages for Nageshwaran, duplicate Ke entry).
- `module5_open_science.tex`: analysis-protocol wording per author; repository statement in the future tense; AI-assistance statement corrected to state that extraction/analysis/drafting were LLM-assisted and that no independent human re-extraction exists yet; Kim Table 16 values are from the arXiv v3, not compared with the published supplement.
- `code/mae_eval`: `pyproject.toml` (editable install dry-run OK; not installed into the shared venv), `cli.py` (`mae-eval audit --log trace.jsonl`, exit codes 0/1/2), `python -m mae_eval`, streaming (`record_stream`) and tool-retry (`record_tool_call`) support, README. Tests: 19 in `tests/test_mae_eval.py` (edge cases: streaming, tool retries, zero-cost, CLI).
- `outputs/maeo_dashboard/index.html`: pure-SVG fallbacks for the Pareto and radar charts when CDN scripts fail (checked in headless Edge with the script tags removed), "Export filtered CSV" button.
- `analysis/assemble_paper.py`: mirrors `manuscript/tables` and `manuscript/figures` into `paper/` so both compile; `\emergencystretch` set.

**Verification:** `assemble_paper.py` -> 22 pages for both `manuscript/main.pdf` and `paper/main.pdf`, 0 LaTeX errors, 0 undefined references/citations, 0 overfull-box warnings, `main.tex` identical in both directories. `pytest tests -q` -> 176 passed (157 existing + 19 mae-eval).

## 2026-11-09 (session 3): figures, citation order, appendices

- Figures 2, 3 (Pareto), 5, 6 redrawn at true print width. `\graphicspath` now searches `figures/` before `../figures/`; the root `figures/` folder held stale copies that LaTeX had been loading.
- Pareto caption and Section 4 text corrected: DyLAN and MAS-Orchestra exceed CoT-SC in accuracy on GPT-5 SMFR (at 2.5x and 1.9x its cost). The -0.053 figure is the mean over three backbones and six frameworks. Removed an unsourced "70% of tokens" claim from Figure 5.
- Bibliography style changed to `unsrtnat` (numbers in order of first citation).
- Abstract: "27.1x median cost" corrected to median 8.1x, mean 27.1x.
- `analysis/run_verified_reml.py` now sweeps phi in {0, 0.25, 0.5, 0.75, 0.9}.
- New: `analysis/make_appendix_tables.py`, `manuscript/appendices.tex` (A: formulations and CR2; B: 17-benchmark ledger and dual-baseline tables; C: mae-eval guide), `code/examples/audit_example.py`, `tests/test_appendix.py`. 180 tests pass; 29 pages; 0 undefined references; 0 overfull boxes.
- CR2 Satterthwaite df across Models A, A', B and phi in [0, 0.9]: 1.00 to 2.14.
- `docs/VENUE_LENGTH_AUDIT.md` added.

## 2026-11-09 (scheduled run, 18:30): provenance, baselines, candidates, protocol

- Tool-use and extraction wording rewritten in `module5_open_science.tex`: extraction and scripts by an AI tool; three kinds of checking distinguished; author second pass "None yet". "Verified" removed from prose (guard test added).
- Jwalapuram Table 4 baseline: "best observed score across MAS system entries" is undefined in the paper and on the project page. All CoT-SC comparisons marked UNRESOLVED; -0.041 removed from the abstract, introduction, Figure 1, Figure 5, discussion, conclusion, and appendix prose. Evidence in `evidence/jwalapuram_baseline_evidence.md`.
- Choi: voting +0.076 recomputed from the source; the debate figure +0.045 is one configuration (decentralized, 2 rounds); +0.030 over three decentralized settings and +0.007 over all nine. Text and Figures 1 and 5 updated.
- Tran: the 96 contrasts use only the Debate and Sequential arms (2 of 5); stated in the text and in Figure 1B and its caption.
- 231 versus 252: 231 appears nowhere as a count; 252 matches the evidence file; see `review/contrast_count_reconciliation.md`.
- Six candidates screened against written criteria (`evidence/eligibility_criteria.md`, `review/candidate_screening.md`): A = Ke, Yang, Zhang, Smit (extracted, not second-passed); B = Chu, Parmar, Wang. Wang's earlier exclusion reason corrected. The manuscript still reports five studies; `review/extension_comparison.md` gives both summaries.
- Purposive-selection paragraph and a candidate table (Appendix) added; no PRISMA.
- `table2_piecewise.tex` moved to `archive/tables/`.
- Draft protocol `protocol/PROTOCOL.md`, tools and 9 tests; nothing run.
- New scripts: recheck_headline_sources.py, extract_extension_studies.py, compare_extension.py, phase2_worksheet.py. 198 tests pass.
