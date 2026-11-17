# Master Unified Implementation Plan: Zero-Deletion Integration of Gemini, Claude (`E1`–`E38`), and ChatGPT (`Parts 1–6`) Audits & Synthesis

## Core Mandate & Guard Invariants
1. **Zero Deletion of Content:** Preserve every existing analysis, equation, proposition, table, figure, and caveat. Improve ordering, add all new tables, derivations, and clarifications from Gemini, Claude, and ChatGPT, and place detailed moderator and framework tables in the Appendix where appropriate.
2. **Workspace Root:** `C:\Users\17756\OneDrive - University of Nevada, Reno\Projects\Automation\01_Research\Manuscripts\01_pure_ml_reasoning_and_test_time_compute`.
3. **Process Safety:** Do not stop, restart, or touch any running `llama-server.exe` process or `outputs/experiments/*.lock`.
4. **Strict Build Gates & Test Guards (`analysis/build_gates.py`, `analysis/assemble_paper.py`, `tests/test_phase15_structure.py`, `tests/test_extension_and_claims.py`):**
   - **G-PLACEHOLDER:** No `\begin{table}...\end{table}` or `\begin{longtable}...\end{longtable}` may contain `in progress` or `\bn/a\b` (case-insensitive). Use `---` or `Introducing` instead of `n/a` inside tables.
   - **G-ABSTRACT:** Every number inside `\begin{abstract}...\end{abstract}` must come from a `\newcommand` macro in `numbers.tex` or `reml_numbers.tex` (only bare digits `95` and `2` are permitted). Preserve `"meanCatA"`, `"meanCatBC"`, `"remlBNineBeta"`, `"sampling gap"`, `"numContrastsZhang"`, and `"without Zhang"` in the abstract, and `"meanJwalapuramSC"` and `"meanJwalapuramCoT"` in the introduction.
   - **G-WUNDERLICH:** No sentence naming `Wunderlich` may use `"equal-compute"`, `"equal compute"`, or `"matched compute"`.
   - **Build Gate 2 Forbidden Words:** Compiled PDF text must contain zero occurrences of `??`, `vc `, `vz `, or capitalized `\bTier\b`, `\bTiers\b`, `\bRegime\b`, `\bRegimes\b`. Use `Category`, `Class`, `Level`, `Group`, or lowercase `tier`/`regime`.
   - **AGENTS.md Style Freeze:** Avoid promotional adjectives, filler adverbs, and forbidden stacked hyphens (`three-level meta-analysis`, `thinking-token parity`, `multi-hop`, `wall-clock latency`, `6-point reviewer checklist`, `5-sample CoT-SC`, `study-weighted mean`, `Leave-one-study-out`, `log-odds ratio`, `MAS-SAS contrasts`).
   - **Phase 15 Structural Guards:** Keep all four `lstlisting` blocks in Appendix D untouched; keep `fig:theory_phase_diagram` and `"fitted to the threshold"` in `section3_theory_revised.tex`; keep `\subsection{The` and `"The segmented regression in \Cref{app:exploratory}"` (and no `"pooled slope difference"`) in `module3_threshold_overhaul.tex`; keep `fig:coordination_taxonomy}` before `\subsection{The PACE Reviewer Checklist}` and keep `tab:cme_card` in `module4_discussion_overhaul.tex`; keep `fig:reml_forest`, `fig:theory_phase_diagram`, and verification sentence counts intact in `appendix_extra.tex`.

---

## Ordered Execution Steps

### Step 0: Write the Master Implementation Plan Artifact & Project Copy
- Write this plan as the conversation artifact `implementation_plan.md` and mirror it to `docs/MASTER_UNIFIED_IMPLEMENTATION_PLAN.md`.

### Step 1: Upgrade `supplement/run_moderator_synthesis.py` & `tests/test_supplement_moderators.py`
1. Replace `supplement/run_moderator_synthesis.py` with a deterministic generator reading `outputs/baseline_tier_contrasts.csv` (832 rows: 358 Category A, 360 Category B, 114 Category C) and `outputs/k9_reml_results.json`, mapping 100% of rows with Haldane–Anscombe log odds ratios, Cohen's $h$, paired binomial noise bands at $\varphi = 0.50$, and paired sampling gaps, writing:
   - `supplement/tables/table_topology_archetypes.tex` (`\label{tab:supp_topology_archetypes}`)
   - `supplement/tables/table_domain_moderators.tex` (`\label{tab:supp_domain_moderators}`)
   - `supplement/tables/table_model_scale_moderators.tex` (`\label{tab:supp_model_scale_moderators}`)
   - `supplement/tables/table_original_vs_audit_quant.tex` (`\label{tab:supp_original_vs_audit_quant}`) with Claude `E2` corrections (splitting Du et al. into `Society of Minds` and `Decentralized debate`, citing only `\citet{liang2023encouraging}` for `Multi-Persona`, splitting `MAS-Orchestra` into introducing vs. later study, using `---` and `Introducing` instead of `n/a`)
   - `supplement/tables/table_adjudication_summary.tex` (`\label{tab:adjudication_summary}`)
   - `supplement/pace_author_template.tex`
   - `supplement/MODERATOR_AND_TAXONOMY_REPORT.md`
   - `supplement/moderator_synthesis_summary.json`
   - Mirror the generated `.tex` tables to `manuscript/tables/`.
2. Update `tests/test_supplement_moderators.py` and verify 100% pass.

### Step 2: Update `analysis/run_k9_reml.py` & `analysis/run_baseline_tiers.py`
1. In `analysis/run_k9_reml.py`:
   - Merge `"Society of Mind"` and `"SoM"` into `"MAD"` ($K = 19$ families), updating `appA_bc_sensitivity.tex` Panel D and caption from `$K = 20$` to `$K = 19$`.
   - Add deduplicated 72-cell Model D REML fit (`D_cells: Baseline-strength check (72 unique cells)`) across all $\varphi$, store in `phi_models`, emit `\remlGapCells*` macros in `reml_numbers.tex`, and add the `D_cells` row to `manuscript/tables/table_k9_reml.tex`.
2. In `analysis/run_baseline_tiers.py`:
   - Add `\textit{$\Delta_{\text{gap}} < 0$}` sub-header on the last column of the Sampling Gap panel in `manuscript/tables/table_baseline_tiers.tex`.
   - Emit macros for Section 5.3 counts in `numbers.tex` (`\numConfigFeasible`, `\pctConfigFeasible`, `\numConfigAhead`, `\pctConfigAhead`, `\numConfigUndet`, `\pctConfigUndet`, `\numSharedCeil`, `\numSharedCeilAhead`, `\pctSharedCeilAhead`, `\numSharedCeilNoHundred`, `\numSharedCeilNoHundredAhead`, `\pctSharedCeilNoHundredAhead`, `\numNoiseBelowBC`, `\numNoiseWithinBC`, `\numNoiseAboveBC`, `\numFeasibleNoiseBelow`, `\numSharedCeilNoiseAbove`).

### Step 3: Bibliography & Related Work Fixes (`manuscript/references.bib`, `manuscript/section2_related_work.tex`)
1. Fix `liang2023encouraging`, `zhuge2023mindstorms`, and `singhal2023towards` in `manuscript/references.bib`.
2. Add `blackwell1953equivalent`, `krogh1994neural`, `ueda1996generalization`, `hong2004groups`, and `manski2003partial` to `manuscript/references.bib`.
3. Apply `E3` in `manuscript/section2_related_work.tex`.

### Step 4: Abstract, Introduction, and Conceptual Framework Upgrades (`manuscript/module1_intro_overhaul.tex`, `manuscript/section3_theory_revised.tex`)
1. Refine flow in `manuscript/module1_intro_overhaul.tex` while preserving every required macro, phrase, empirical example, and contribution item (`E19`–`E20`).
2. Upgrade `manuscript/section3_theory_revised.tex` with the Three-channel roadmap, `E28`, `E13`–`E15`, $\Delta_{\text{baseline}}$ vs. $\Delta_{\text{frontier}}$, `manski2003partial`, Prop. 3.1 joint readout + `blackwell1953equivalent`, `E8`–`E12`, `E16`–`E17`, Route II/III precision + `hong2004groups`, and the PACE Master Reference Table (`\label{tab:pace_master_reference}`).

### Step 5: Empirical Synthesis, Adjudication Table, Moderator Summary & Objections (`manuscript/module2_empirical_overhaul.tex`, `manuscript/module3_threshold_overhaul.tex`)
1. Apply `E1`, `E4`, `E5`, `E14`, `E16`, `E18` (sub-headings, `\Cref{eq:noise_band}`, `\Cref{tab:adjudication}`), `E22`, `E31` (`(vii)–(xii)`), `$K=19$`, `E7`, and a concise moderator synthesis paragraph referencing `\Cref{tab:supp_topology_archetypes,tab:supp_domain_moderators,tab:supp_model_scale_moderators}`.
2. Apply `E30` in `manuscript/module3_threshold_overhaul.tex`.

### Step 6: Discussion, Route Tests, Minimum Viable PACE Audit, Appendix Tables & Layout Polish (`manuscript/module4_discussion_overhaul.tex`, `manuscript/module6_conclusion_overhaul.tex`, `manuscript/appendix.tex`, `analysis/assemble_paper.py`)
1. Add Four-Case paragraph in `§6.1`, `tab:route_tests` + `PACE decision rules` box (`E38`) in `§6.2`, `E21` + `Minimum Viable PACE Audit` box + three reporting levels (`PACE-Minimum`, `PACE-Recommended`, `PACE-Extended`) in `§6.3`, ensemble covariance (`krogh1994neural,ueda1996generalization`) in `§6.5`, and `E22` in `§6.4` and `§7`.
2. Add `\raggedbottom` in `assemble_paper.py`; in `appendix.tex`, add `\counterwithin{table}{section}` and `\counterwithin{figure}{section}`, apply `E14a`, `E9`, `E10`, `E17`, `E34`, `eq:noise_band`, `E6`, $K=19$ family list, `E36` (`\clearpage` removal + range fix), `E2` (`tab:original_vs_audit` + `table_original_vs_audit_quant.tex`), `E35` (`tab:appB_hetermad`), and `\subsection{Moderator Synthesis by Topology, Task Domain, and Model Scale}\label{sec:appendix_moderators}`.

### Step 7: Full Build & Verification Suite
1. Execute `analysis/run_baseline_tiers.py`, `analysis/run_k9_reml.py`, and `supplement/run_moderator_synthesis.py`.
2. Execute `analysis/assemble_paper.py` and verify all 4 PDFs pass all gates.
3. Run the full `pytest` verification suite and inspect `manuscript/tmlr_submission.log` for zero unresolved citations or references.


---

## Phase 16 Gold-Standard Methodological Bulletproofing & Strategy Integration (2026-11-15)

### Reference Artifact
- Full diagnostic forecast matrix, 2026–2035 citation scenarios, Landmark Gap Matrix, canonical denominator ledger (`12 / 9 / 531 / 516 / 834 / 474 / 156 / 318 / 72 / 19`), and mathematical guardrails archived in [ACCEPTANCE_AND_CITATION_STRATEGY_2026_2035.md](../docs/ACCEPTANCE_AND_CITATION_STRATEGY_2026_2035.md).

### Execution Steps (Preserving Zero-Deletion, AI-Disclosure Invariance, and 23-Macro Repeat Ledger)
1. Synchronize `"Sampled"` vs. `"Sample-matched"` across `analysis/run_baseline_tiers.py`, regenerated `manuscript/tables/table_baseline_tiers.tex`, and `paper/tables/table_baseline_tiers.tex`.
2. Clean up stacked hyphens in `manuscript/module1_intro_overhaul.tex` and `manuscript/module6_conclusion_overhaul.tex`, spotlight progressive reporting levels (`PACE-Minimum`, `PACE-Recommended`, `PACE-Extended`) and nested initial-round voting, keeping zero bare digits and identical macros.
3. Refine `manuscript/section3_theory_revised.tex`: standardize $\mathcal{H}^{(T)}$ notation in Proposition 3.1, apply Rule C.5 factual caption on `fig:waterfall`, and clean stacked hyphens.
4. Upgrade `manuscript/module2_empirical_overhaul.tex`: integrate defensive paragraphs for hostile Attacks 1–6 & 8, unified counting conventions, three-unit roadmap at start of Section 5.3, cross-link to `tab:pace_subfield_hooks`, factual Rule C.5 caption on `fig:reml_forest`, and `"Sampled"` naming without adding/removing macros.
5. Upgrade `manuscript/module4_discussion_overhaul.tex` and `manuscript/module5_open_science.tex`: Four-Case diagnostic synthesis in Section 7.1, testable operational design objectives ($\Delta_{\mathrm{arch}} > \Delta_{\mathrm{overhead}}$, $\Delta p_{\mathrm{ver}} > \Delta p_{\mathrm{agg}}$, $\Delta C < 0$, separated state), Attack 9 & 10 defenses, and 7th operational row (`Resource distribution and stopping`) in `tab:cme_card`.
6. Expand `manuscript/appendix_extra.tex` (community hooks table `tab:pace_subfield_hooks`, Attack 7 tuning-budget note `(xiii)`, constructive design equations, operational per-item $k_i$ / adaptive stopping / cache-adjusted billing-equivalent tokens / directed call-graph hybrid classification) and enforce strictly factual Rule C.5 captions in `analysis/assemble_paper.py`.
7. Verify `analysis/make_claims_ledger.py`, `analysis/make_repeat_targets.py` (`23 macros`), `analysis/assemble_paper.py` (all 4 PDFs pass Build Gates 1–3), and full `pytest -q tests/`.
