# Current Project Audit & Inventory (Phase 0 Deliverable)

**Date:** November 10, 2026  
**Repository Working Directory:** `Automation/01_Research/Manuscripts/01_pure_ml_reasoning_and_test_time_compute`  
**Git Branch:** `main` (clean working state prior to documentation release; commit `51282b1`)  
**Target Submission:** Transactions on Machine Learning Research (TMLR) / Primary Conferences (ICLR, NeurIPS, ACL)

---

## 1. Executive Summary & Verification State

This audit inventories the current scientific, empirical, software, and manuscript assets of the project:
*"More Agents, More Samples, or More Thinking? Untangling Coordination, Ensembling, and Test-Time Compute in Multi-Agent LLMs"*.

The objective is to establish an unvarnished baseline of:
1. What is mathematically and empirically demonstrated vs what remains an assumption.
2. What software is functional vs what remains prototype or synthetic.
3. What literature evidence is rigorously verified vs what requires further extraction and protocol expansion.

---

## 2. Manuscript Build & Artifacts

| Artifact | Source File | Compiled PDF | Pages | Compilation Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Preprint Target** | `manuscript/main.tex` | `manuscript/main.pdf` | 35 | 0 errors, 0 undefined references, 0 overfull boxes |
| **TMLR Submission Target** | `manuscript/tmlr_submission.tex` | `manuscript/tmlr_submission.pdf` | 31 | Double-blind compliant; ~13 pages main text body |
| **Assembly Script** | `analysis/assemble_paper.py` | — | — | Executes cleanly via Python 3.12 |

### Key Prose & Mathematical Upgrades (Commits `83f6805`, `c1c79de`, `bc438c8`):
- **Resource Vector:** Formally defined as $\mathbf{R} = (R_{\text{in}}, R_{\text{out}}, R_{\text{reason}}, R_{\text{cost}}, R_{\text{lat}}, R_{\text{calls}})$.
- **Constrained Frontier:** Defined as $f(\mathcal{B}; t, m) \triangleq \sup_{\pi \in \Pi_{\text{indep}}, \mathbb{E}[\mathbf{R}(\pi)] \le \mathcal{B}} \mathbb{E}[\operatorname{Accuracy}(\pi; t, m)]$.
- **Coordination Premium:** $\Gamma(\mathcal{B}; t, m) \triangleq \mathbb{E}[\operatorname{Accuracy}(\pi_{\text{comm}}^*; t, m)] - f(\mathcal{B}; t, m)$.
- **Pairwise Coordination Delta:** $\Delta_{\text{comm}}(\pi_{\text{comm}}, \pi_{\text{indep}}; \mathcal{B}, t, m) \triangleq \mathbb{E}[\operatorname{Accuracy}(\pi_{\text{comm}})] - \mathbb{E}[\operatorname{Accuracy}(\pi_{\text{indep}})]$, strictly requiring $\mathbb{E}[\mathbf{R}(\pi_{\text{comm}})] \le \mathcal{B}$ and $\mathbb{E}[\mathbf{R}(\pi_{\text{indep}})] \le \mathcal{B}$ along named resource dimensions.
- **Sampling Gap Identity:** $\Delta_{\text{gap}} = (p_{\text{MAS}} - p_{\text{sampled}}) - (p_{\text{MAS}} - p_{\text{single}}) = p_{\text{single}} - p_{\text{sampled}}$. Multi-agent performance cancels algebraically, establishing that the metric measures empirical baseline strengthening rather than a causal coordination mechanism.
- **Four-Category Baseline Taxonomy:**
  - *Category A:* Greedy Single-Pass ($N=1, T=1$).
  - *Category B:* Sample-Matched ($k$-sample self-consistency; compute/tokens unconstrained; never called compute-matched).
  - *Category C:* Resource-Matched (matched thinking tokens, iterations, or monetary cost).
  - *Category D:* Pareto Frontier Sweep.

---

## 3. Empirical Evidence Base (Dataset B & Audit Ledger)

### Current Study Corpus:
- **Included Studies:** 9 papers (Choi et al., Tran et al., Kiela et al., Jwalapuram et al., Kim et al., Smit et al., Zhang et al., Yang et al., Li et al.).
- **Total Contrasts:** 531 individual contrast pairs synthesized across benchmarks (GSM8K, MATH, HumanEval, MMLU, StrategyQA).
- **Core Ledger Files:**
  - `evidence/extension_contrasts.csv` (531 rows)
  - `evidence/verification_worksheet.csv` (complete metadata and verification status)
  - `evidence/spot_check_ledger.csv` (40-contrast stratified verification audit)

### Verification Ledger Audit:
- **Sample:** Stratified audit of 40 contrasts across all 9 studies.
- **Concordance:**
  - 21/40 contrasts matched both exact numerical table values and published text labels.
  - 19/40 contrasts matched the numerical value printed on the page, but exhibited minor label/table header variations.
  - 5 previously flagged scrambled table rows (Jwalapuram Table 4 p.16, Kim Table 16 p.43 [3 rows], Yang Table 1 p.6) were manually cross-checked against PDF renderings and verified correct.
- **Identified Evidence Limitations:**
  1. Initial corpus selection was a structured convenience sample rather than an exhaustive systematic review protocol.
  2. Plot-only studies (e.g. Wang et al., EMNLP 2024) were excluded due to unextracted raw numerical data.
  3. Only Tran & Kiela strictly enforced token budgets in Tier B; other studies varied in token accounting.
  4. Positive matched-budget results from 2026 (Wunderlich et al., ColMAD) require formal tabular inclusion into the quantitative synthesis.

---

## 4. Software & Tooling Audit (`code/`)

### A. CME Evaluation Toolkit (`code/mae_eval`)
- **Package Status:** Valid Python package with `pyproject.toml` and CLI entry points.
- **Modules:**
  - `vector.py`: Implements 6D resource vector with dominance comparisons and Pareto filtering. (Functional, verified by tests).
  - `tracker.py`: Tracks token usage, latency (serial vs parallel), and estimated monetary costs per call. (Functional).
  - `auditor.py`: Classifies parity status into:
    - `strictly_controlled`
    - `approximately_controlled`
    - `measured_unmatched`
    - `unreported`
    - `not_applicable`
  - `cli.py`: Command-line interface for running audits and summaries.
- **Gaps in Current Software:**
  - No direct local inference runner for Ollama models (currently relies on structured JSON inputs or mock drivers).
  - Automated BenchmarkExporter to export to external benchmark formats is not yet implemented.

### B. Calibration Runner (`code/run_calibration_anchor.py`)
- **Current Status:** **SYNTHETIC SIMULATION ONLY**.
- **Assessment:**
  - Generates synthetic binary item outcomes using a latent difficulty model where $\phi$ is forced to $0.50$ by construction ($\alpha = \sqrt{\phi / (1 - \phi)}$).
  - The manuscript has been corrected to explicitly state that this protocol is synthetic and that empirical $\phi$ between single-agent and multi-agent systems remains unmeasured.
- **Action Required:** Build a live runner executing local open-weight models (Qwen, Gemma, Llama) over GSM8K to calculate true empirical $\phi$.

### C. Sampling Gap Accounting (`code/sampling_gap.py`)
- **Current Status:** Fully verified. Confirms algebraic cancellation identity across varying baseline accuracies.

---

## 5. Test Suite Verification (`tests/`)

- **Total Test Files:** 12 files.
- **Total Tests:** 206 tests.
- **Test Categories:**
  - `test_extension_and_claims.py`: 10 claim-integrity tests verifying that no unsupported "verified compute-matched" or "first" claims appear in the LaTeX manuscript.
  - `test_mae_eval.py`: 48 tests validating the resource vector, tracking, and auditing engine.
  - `test_meta_analysis.py`: 32 tests verifying REML estimation, Haldane-Anscombe corrections, and meta-analytic aggregations.
  - `test_figures.py`: 16 tests verifying DPI ($\ge 300$), PDF/PNG/SVG header signatures, and generation.
  - `test_sampling_gap.py`: 12 tests verifying identity arithmetic.
  - `test_audit_trail.py` & `test_pipeline.py`: Pipeline integration and audit consistency.

---

## 6. Style & Compliance Audit (`AGENTS.md`)

- **Banned Adverbs & Adjectives:** Scanned and purged from `manuscript/` (zero occurrences of *groundbreaking*, *novel*, *revolutionary*, *unprecedented*, *rigorous*, *principled*, *primarily*, *systematically*, *substantially*).
- **Hyphenation Directives:** All stacked hyphens resolved into plain prepositional phrases (*multilevel meta-analysis with three levels*, *budget of thinking tokens*, *execution latency*). Hyphens preserved only in standard technical compounds (*multi-agent*, *single-agent*, *self-consistency*, *chain-of-thought*, *meta-analysis*, *cluster-robust*).
- **Figure Captions:** Stripped of promotional and interpretive language; restricted strictly to variables, conditions, and sample sizes plotted.
- **Double-Blind Integrity:** Clean for TMLR submission (`tmlr_submission.tex` contains no author identifiers, institution mentions, or active public repository URLs).

---

## 7. Immediate Phase 1 & 2 Priorities

1. **Novelty & Competitor Matrix (`docs/RELATED_WORK_AND_NOVELTY_MATRIX.md`):** Complete exhaustive comparison against 14 papers and 6 agent evaluation platforms.
2. **Systematic Literature Protocol (`evidence/literature_screening_ledger.csv`):** Formulate formal PRISMA-style search queries across arXiv, OpenReview, and ACL Anthology through Nov 10, 2026.
3. **Live Calibration Runner (`code/run_calibration_live.py`):** Implement live Ollama inference runner on RTX 4070 to measure empirical $\phi$ on 300 GSM8K items.
4. **Digitized Plot Tier:** Digitize Wang et al. (EMNLP 2024) token-economy plots with explicit confidence bounds.
