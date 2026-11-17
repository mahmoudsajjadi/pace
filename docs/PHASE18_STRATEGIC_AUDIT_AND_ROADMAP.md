# Phase 18 Strategic Audit & Roadmap (2026--2035)

**Frozen Paper Title:** *More Agents, More Samples, or More Thinking? Untangling Coordination, Ensembling, and Test-Time Compute in Multi-Agent LLMs*  
**Framework:** PACE (*Parity-Aware Compute Evaluation*)  
**Scope:** Comprehensive research-quality audit, TMLR/J2C certification strategy, software adoption roadmap, and citation-growth plan through 2035.

---

## 1. Senior-Reviewer Critique Summary & Substantive Fixes

### Key Scientific & Methodological Critiques
1. **Abstract Necessity Claim vs. Bounded Computation:**
   - *Issue:* The abstract's necessity claim ("positive returns require partitioned evidence, external verification, or error diversity across models") is stronger than Proposition 3.1, which bounds *information*, not *bounded-LLM computation*.
   - *Fix:* Replace with: *"Under redundant evidence, communication cannot increase the information available about the target beyond the shared input. Whether it improves accuracy at fixed resources remains a question of computational efficiency. Partitioned evidence, verification, and model diversity are candidate mechanisms for positive returns, not established necessary conditions."*
2. **Non-Systematic Study Selection & Plot-Only Exclusions:**
   - *Issue:* Purposive selection of 5 initial studies + 7 screened candidates; *Reasoning in Token Economies* (Wang et al., EMNLP 2024) excluded because results are in plots.
   - *Fix:* Execute reproducible API PRISMA search (`scripts/prisma_search.py` + `scripts/screen_literature.py`), register `docs/PREREGISTRATION_PRISMA_REVIEW.md` on OSF, and digitize plot-only predecessors in a sensitivity analysis.
3. **Estimand Clarity ("Coordination Effect" vs. "Architecture Premium"):**
   - *Issue:* Equation 4 labels $p_A - f(B_A)$ a coordination effect, which mixes communication with prompts, tools, and optimization effort.
   - *Fix:* Separate **Architecture Premium** (MAS minus strongest fair non-communicating comparator) from **Communication Effect** (controlled intervention on message exchange with all else fixed, including semantic-placebo controls).
4. **Baseline Taxonomy Axes:**
   - *Issue:* Categories A--D overlap (e.g., agent-count matching vs. forward-pass matching; frontier sweeps vs. pairwise baselines).
   - *Fix:* Clarify three orthogonal axes: (1) Baseline strategy, (2) Matched resource controls, and (3) Evaluation design (operating point vs. sweep vs. validation-selected frontier).
5. **Statistical Dependence, Unknown $N$, & Sensitivity Bounds:**
   - *Issue:* 516 configurations across 9 studies (Category C has 2 studies); `N=100` placeholder for Zhang et al. AGIEval; whole-study correlation sensitivity yields slightly positive upper CR2 CI limits.
   - *Fix:* State equal-study-weighted means (`-0.038`) alongside contrast-weighted means (`-0.042`) in the Abstract; mark unknown $N$ explicitly and exclude from precision-weighted inference; reconcile abstract sensitivity wording with positive upper CI limits.
6. **Missing `Heter-MAD` Extraction & Per-Contrast Pareto Check:**
   - *Fix:* Extract Zhang et al. Table 4 (`Heter-MAD`) into Appendix B.4; verify $\mathbf{R}_{\text{SAS}} \le \mathbf{R}_{\text{MAS}}$ contrast-by-contrast across all 474 Category B/C rows.
7. **Live LLM Validation & Software Interoperability:**
   - *Fix:* Run live Experiments A--C (homogeneous vs. heterogeneous, shared vs. partitioned hidden-profile, verifier gating, real traces) and align PACE with OpenTelemetry GenAI spans / Rollout Cards / `inspect_ai` / `lm-evaluation-harness`.

---

## 2. Priority Order (Execution Sequence)

1. **P0 (Same-Day Non-GPU Fixes):**
   - Fix 4 typos (`Kim et al..`, `per characterize`, `\varphi \in [0.00, 0.90]`, Figure 4 left padding).
   - Per-contrast Pareto check in `analysis/run_baseline_tiers.py`.
   - Extract Zhang et al. Table 4 (`Heter-MAD`) into Appendix B.4.
   - Reconcile abstract necessity claim, study-weighted mean (`-0.038`), and sensitivity CI wording.
   - Register `docs/PREREGISTRATION_PRISMA_REVIEW.md` on OSF.
2. **P1 (Live Validation & Systematic Search):**
   - Run `scripts/prisma_search.py` & `scripts/screen_literature.py` (with independent second-rater audit on a 20%--40% sample).
   - Run live LLM calibration & Hidden-Profile $2\times 2$ experiments; inject real traces into Appendix D.1.
   - Package 1-command `Makefile` / `reproduce_all.sh` and publish `pace-eval` on PyPI.
3. **P2 (TMLR Submission & Ecosystem Adoption):**
   - Submit anonymized `tmlr_submission.pdf` to TMLR with Survey / Reproducibility / Featured (J2C) certification requests (check ICLR 2027 J2C deadline: Dec 18, 2026).
   - Publish Hugging Face Dataset + Space, `pace.autolog()` adapters, and `lm-evaluation-harness` / `inspect_ai` PRs.

---

## 3. Target Strategy Deliverables (`arxiv_version/strategy/`)

When executing the full strategic audit, generate the 18 strategy reports in `arxiv_version/strategy/`:
1. `ACCEPTANCE_AND_REVIEW_ASSESSMENT.md`
2. `CERTIFICATION_AND_CONFERENCE_PATHWAYS.md`
3. `CRITICAL_REVIEW.md`
4. `LITERATURE_SEARCH_PROTOCOL.md`
5. `EVIDENCE_CORPUS_EXPANSION.md`
6. `HETER_MAD_ANALYSIS_PLAN.md`
7. `EXPERIMENT_PROTOCOL.md`
8. `PACE_PRODUCT_ROADMAP.md`
9. `PACE_SCHEMA_SPECIFICATION.md`
10. `PACE_INTEGRATION_MATRIX.md`
11. `PACE_REPRODUCIBILITY_CHECKLIST.md`
12. `BOTTLENECKS_AND_SOLUTIONS.md`
13. `CITATION_FORECAST_2026_2035.md`
14. `CITATION_FORECAST_2026_2035.csv`
15. `CITATION_GROWTH_PLAN.md`
16. `VENUE_AND_PRESENTATION_STRATEGY.md`
17. `V2_V3_EXECUTION_ROADMAP.md`
18. `STRATEGIC_EXECUTIVE_SUMMARY.md`
