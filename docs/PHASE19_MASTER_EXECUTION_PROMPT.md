# Phase 19: Master Execution Prompt & Strategic Mission

> **Context:** Saved verbatim as the authoritative master execution specification for `arXiv v2`, TMLR review & certification, live empirical validation, PACE software maturity, and 2026--2035 citation-growth strategy.

---

## Key Built-In Corrections

1. **ICLR 2027 J2C Conditional Timing:** The J2C request deadline is **December 18, 2026** (capacity 150), and requires the paper to already be **published** in TMLR with a qualifying certification (J2C, Featured, or Outstanding). An acceptance email alone is insufficient. Inspect the actual TMLR review stage before recommending this route.
2. **TMLR Survey Policy (Effective September 1, 2026):** TMLR no longer considers survey papers for review, but accepts original empirical studies, new analytical frameworks, and methods for assessing performance. Position the manuscript as an **original empirical and methodological study** (not a survey), and do not rely on Survey Certification for a new submission.
3. **P0 AI-Use Disclosure Reconciliation:** Reconcile the discrepancy between the current arXiv PDF (*"generative AI and large language models were used solely for language editing and grammar checking"*) and the earlier TMLR draft (*AI-assisted literature screening, table extraction, and automated concordance checks, plus a 40-contrast stratified audit*).

---

## Master Execution Specification

- **Project Directory:** `C:\Users\17756\OneDrive - University of Nevada, Reno\Projects\Automation\01_Research\Manuscripts\01_pure_ml_reasoning_and_test_time_compute\`
- **Output Directory:** `arxiv_version/` (with `strategy/`, `research_data/`, `experiments/`, `logs/`)
- **Frozen Title:** *More Agents, More Samples, or More Thinking? Untangling Coordination, Ensembling, and Test-Time Compute in Multi-Agent LLMs*
- **Author:** Seyed Mahmoud Sajjadi Mohammadabadi (`mahmoud.sajjadi@unr.edu`, Department of Computer Science and Engineering, University of Nevada, Reno, NV 89557, USA)
- **Repository:** `https://github.com/mahmoudsajjadi/pace`
- **Non-Negotiable Safety Rules:**
  - Preserve the original TMLR submission untouched.
  - No external submissions, no public dataset/DOI/PyPI/GitHub pushes, no paid API calls without explicit authorization.
  - No fabricated data, placeholder sample sizes treated as verified, synthetic traces presented as live runs, or invented acceptance/certification probabilities.

### Execution Phases (0--11)
- **Phase 0:** Inventory and preservation (Git status, hashes, immutable backup of TMLR submission).
- **Phase 1:** Version comparison and AI-use disclosure audit (`AI_USE_DISCLOSURE_AUDIT.md`, `ARXIV_METADATA_VALIDATION.md`).
- **Phase 2:** Scientific and mathematical review (`CRITICAL_REVIEW.md`, `CONTRIBUTION_BY_CONTRIBUTION_AUDIT.md`, novelty matrix vs. Rollout Cards / OpenTelemetry / Inspect AI / LangSmith / Langfuse).
- **Phase 3:** Evidence corpus and reproducible literature search (`candidate_studies.csv`, `screening_decisions.csv`, `expanded_extraction.csv`, `study_metadata.csv`, `source_verification_ledger.csv`).
- **Phase 4:** Statistical reanalysis (`STATISTICAL_REANALYSIS_REPORT.md`: separate Category B & C, study-equal vs. contrast-weighted, unknown-$N$ handling, sensitivity bounds).
- **Phase 5:** `Heter-MAD` extraction (`heter_mad_extraction.csv`, `HETER_MAD_ANALYSIS_PLAN.md`).
- **Phase 6:** Experiment design and local pilot (`EXPERIMENT_PROTOCOL.md`, E1--E14 matrix, live local-model traces).
- **Phase 7:** PACE software audit and improvements (`PACE_PRODUCT_ROADMAP.md`, `PACE_SCHEMA_SPECIFICATION.md`, `PACE_INTEGRATION_MATRIX.md`, `PACE_REPRODUCIBILITY_CHECKLIST.md`).
- **Phase 8:** Acceptance, certification, and venue analysis (`ACCEPTANCE_AND_REVIEW_ASSESSMENT.md`, `CERTIFICATION_AND_CONFERENCE_PATHWAYS.md`, `VENUE_AND_PRESENTATION_STRATEGY.md`).
- **Phase 9:** Citation forecast and adoption strategy (`CITATION_FORECAST_2026_2035.md`, `CITATION_FORECAST_2026_2035.csv`, `citation_comparison.csv`, `CITATION_GROWTH_PLAN.md`, `BOTTLENECKS_AND_SOLUTIONS.md`).
- **Phase 10:** arXiv package preparation and compilation (`README_ARXIV.md`, `ARXIV_METADATA.md`, `CHANGELOG_ARXIV.md`, `VALIDATION_REPORT.md`).
- **Phase 11:** Final validation and executive report (`V2_V3_EXECUTION_ROADMAP.md`, `STRATEGIC_EXECUTIVE_SUMMARY.md`, `MASTER_STRATEGY.md`, `UNRESOLVED_ISSUES.md`).
