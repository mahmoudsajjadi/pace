# PACE PARALLEL MASTER SCHEDULE v3.2 (Dual-Track GPU + CPU Execution Starting Friday, Nov 13, 2026 at 6:00 PM)

Project: `C:\Users\17756\OneDrive - University of Nevada, Reno\Projects\Automation\01_Research\Manuscripts\01_pure_ml_reasoning_and_test_time_compute`

Read first: `AGENTS.md`, `../../AGENTS.md`, `PROJECT_STATE.md`, `analysis/build_gates.py`, `analysis/assemble_paper.py`, `analysis/run_sampling_gap_unique_cells.py`, `analysis/run_b9_prediction_and_merged_cluster.py`, and `analysis/propose_category_rename.py`.

---

### PARALLEL EXECUTION & QUOTA-PROTECTION RULES (CRITICAL)
1. **NEVER Block or Poll on GPU Inference:** Whenever an LLM experiment or pilot is launched, start it as a **detached background process** (writing to append-only `.jsonl` logs with a `.lock` file and PID recorded in `STATUS.md`). NEVER sleep-loop waiting for an LLM run to finish—immediately move to the next CPU/manuscript/statistical task! Check background job progress only once at the top of each hour via fast line counts (`wc -l`).
2. **One Writer on Manuscript & Core Scripts, Parallel Subagents on Isolated Outputs:**
   - Only you (the main agent) may edit `manuscript/`, `numbers.tex`, `reml_numbers.tex`, `analysis/assemble_paper.py`, and `code/`.
   - You MAY spawn parallel background subagents for **read-only or isolated-file tasks** that never touch `manuscript/`: (a) rendering source PDF crops into `review/crops/`, (b) building `reports/number_ledger.csv`, (c) verifying bibliographic metadata into `reports/bibliography_check.md`, and (d) running Monte Carlo estimator simulations into `outputs/simulation_results.json`.
3. **Hourly Checkpoints:** At the end of every 1-hour block, run `pytest -q`, check background GPU line counts, write `reports/HOUR_<XX>.md`, update `STATUS.md`, and make a local git commit on branch `pace-v3`.
4. **Preserve TMLR Guardrails:** Keep the Page-1 `\thanks{AI tools ...}` footnote intact (`G-THANKS`) and keep the truthful `VERIF` statement until the human author signs `review/HAND_VERIFICATION_CHECKLIST.md`.

---

## DAY 1: FRIDAY, NOV 13 (6:00 PM – 12:00 AM) — LAUNCH GPU QUEUE + FIX ALL CODE, STATS & MANUSCRIPT BUGS IN PARALLEL

### HOUR 1 (6:00 PM – 7:00 PM): Branch Setup, Fix Experiment/Dynamics Code FIRST, and Launch Detached GPU Queue
Because GPU inference takes hours, fix the experiment/dynamics code in the first 30 minutes so the GPU can run continuously in the background while you do CPU/manuscript work:
1. Checkout branch `pace-v3` and move legacy `apply_*burstiness*` / `apply_style_cleanup*` scripts to `archive/`.
2. **Fix `code/pace/dynamics.py` (Adjacent-Round Transition Rates):** Update `pace dynamics` so transition rates $\hat{\tau}_{i\to c}$ and $\hat{\tau}_{c\to i}$ are computed across **adjacent rounds** ($r_t \to r_{t+1}$, recovering $\approx 0.30$ and $\approx 0.10$ per round on `sample_debate_dynamics.jsonl`) in addition to reporting first-to-last net flips. Verify `S4v` (verifier-gated arm) and `ResourceTracker` (logging independent draws $R_{\mathrm{sample}} = k$ separately from total LLM calls $N_{\mathrm{calls}}$ and judge calls) pass `pytest -q`.
3. **LAUNCH TRACK A (Detached Background GPU Runner):**
   - Check `outputs/experiments/confirmatory/llama3.1-8b__hidden_profile/results.jsonl`. If incomplete, resume it in the background and chain the **50-item 6-arm pilot** (`Greedy`, `Sampled Pool k=1..32`, `Extended Thinking`, `Debate 5x3`, `No-Comm Control`, `Placebo Debate`) on `llama3.1:8b` right behind it in a detached background script (`scripts/run_gpu_queue.py`).
4. **LAUNCH SUBAGENT C1 (Parallel Read-Only):** Build `reports/number_ledger.csv` mapping every number in `tmlr_submission.pdf` -> macro -> script -> recomputed value.
5. Commit `reports/HOUR_01.md`.

### HOUR 2 (7:00 PM – 8:00 PM): Fix All 7 Manuscript/Script Bugs & Unify Resource Vector $\mathbf{R}$ (While GPU Runs)
1. Check Track A GPU log line counts (2 seconds; do not block).
2. **LAUNCH SUBAGENT C2 (Parallel Isolated Output):** Crop every source PDF table region for the 474 Category B/C contrasts into `review/crops/` and build `review/hand_check.csv` + `review/second_rater_sheet_blank.csv` (never pre-fill human rater columns).
3. **Fix the 7 Bugs in `manuscript/` and `analysis/assemble_paper.py`:**
   - `manuscript/section2_related_work.tex` (Page 4): Remove duplicate `"at comparable compute read off Pareto fronts"` in Para 3; fix `"source-accounting"` -> `"resource-accounting"` in Para 5.
   - `manuscript/appendix_extra.tex` (Page 40, E.7): Fix `review/AI_ASSISTED_EXTRACTION_AUDIT. _EXTRACTION_AUDIT.md` -> `review/AI_ASSISTED_EXTRACTION_AUDIT.md`.
   - `analysis/assemble_paper.py` (lines 79 & 283): Replace `https://github.com/cme-eval/cme` and `CME Reviewer Checklist` with `https://github.com/mahmoudsajjadi/pace` and `PACE Reviewer Checklist`; sync `pdfkeywords`.
   - **Unify $\mathbf{R}$ in Section 4 (`module2_empirical_overhaul.tex`) & Appendix A.1 (`appendix.tex`):** Define $R_{\mathrm{sample}}$ everywhere as **independent trajectories/samples drawn ($k$)** (with total LLM calls $N_{\mathrm{calls}}$ logged separately, and judge calls counted in $N_{\mathrm{calls}}$ and $R_{\mathrm{token}}$, never in $R_{\mathrm{sample}}$). Define $R_{\mathrm{sys}}$ everywhere as **external tool, compiler, retrieval, or verifier invocations** (scaffolding tokens are $\tau_{\mathrm{scaff}} \subset R_{\mathrm{token}}$).
4. Run `pytest -q` and commit `reports/HOUR_02.md`.

### HOUR 3 (8:00 PM – 9:00 PM): Category B/C Crosswalk + Arm Overnight GPU Confirmatory Queue
1. Check Track A GPU log line counts. If the 50-item pilot finished, run `analysis/power_planning.py` on the pilot discordance and **arm the Overnight Detached GPU Queue** (`GSM8K` & `MATH-500` 6-arm shared-evidence runs + Route II Python-verifier-gated debate vs. verifier-gated sampling + `deepseek-r1:14b` / `qwen2.5:7b` replication) so the GPU runs non-stop overnight!
2. **Refine Baseline Ladder (Section 3.5, Figure 1, Table 2, Figure 4, Figure 5):**
   - Category A: Greedy single pass ($N=1, T=1$).
   - Category B: Sampled, unmatched baseline ($k$ samples; tokens/calls/cost not verified equal).
   - Category C: Single-resource-matched baseline (one declared resource or ceiling held equal: thinking tokens in Tran, iterations in Kim, 16-generation ceiling in Yang).
   - Category D: Pareto frontier sweep.
3. Update `analysis/propose_category_rename.py` and `analysis/run_baseline_tiers.py` moving **Yang et al. (42 contrasts)** from B to C while keeping **Choi et al. (14 contrasts)** in B (and reporting the sensitivity if Choi moves to C). Sweep the text to replace any unqualified `"holds compute constant"` or `"equal compute"` with the specific matched resource.
4. Commit `reports/HOUR_03.md`.

### HOUR 4 (9:00 PM – 10:00 PM): Integrate 72 Unique Baseline Cells (`run_sampling_gap_unique_cells.py`)
1. Check Track A GPU log line counts.
2. Integrate the verified results of `analysis/run_sampling_gap_unique_cells.py` (`outputs/sampling_gap_unique_cells.json`) into Section 5.3 (`Sampling gap`), Table 2, and Section 5.4 / Table 3 (`Model D`).
3. Report both the **72 unique `(study, benchmark, model)` baseline cells** (Jwalapuram 18, Zhang 28, Smit 7, Ke 5, Choi 14; $-0.038$ study-equal mean, sampled baseline stronger in all 5 studies, primary cell-level Model D REML fit) and the 318 MAS-linked pairs.
4. Commit `reports/HOUR_04.md`.

### HOUR 5 (10:00 PM – 11:00 PM): Integrate Prediction Intervals, 7-Cluster Jwalapuram+Ke Merge & Exclusions
1. Check Track A GPU log line counts.
2. **LAUNCH SUBAGENT C3 (Parallel Isolated Output):** Run `scripts/run_estimator_simulations.py` (Monte Carlo validation of frontier-gap bootstrap coverage and CR2 small-sample interval coverage) and save to `outputs/estimator_simulations.json`.
3. Integrate the verified outputs of `analysis/run_b9_prediction_and_merged_cluster.py` (`outputs/b9_prediction_and_merged_cluster.json`):
   - Add the **95% prediction interval** for a new study's true mean ($[-0.515, +0.125]$ on the log-odds scale) to Section 5.4 and Table 3.
   - Add the **7-cluster merged Jwalapuram+Ke sensitivity fit** (4 shared authors + shared GPQA/BrowseComp+ benchmarks) to Table 5 (Appendix A.3).
   - Add sensitivity rows excluding (i) AGIEval placeholder $N=100$ rows, (ii) Jwalapuram upper-bound CoT-SC rows, and (iii) Tran 100-token truncated rows.
4. Commit `reports/HOUR_05.md`.

### HOUR 6 (11:00 PM – 12:00 AM): Theory Upgrades (Prop. 3.2 Multi-Class Proof & Prop. 3.3 Martingale Connection) + Overnight GPU Lock Check
1. In `manuscript/section3_theory_revised.tex` and `manuscript/appendix.tex`:
   - Rename Proposition 3.2(1) to `"Majority-vote amplification over a single random draw"`, add and prove the multi-class extension ($1 - (|\mathcal{Y}|-1)\exp(-Kd^2/2)$ when the correct class leads every wrong class by margin $d > 0$), and cite **Chen et al. (2024)** (*Are More LLM Calls All You Need?*) to explain fixed-item monotonicity vs. aggregate non-monotonicity across heterogeneous item difficulties.
   - Relate Proposition 3.3 to **Theorem 2 of Choi et al. (2025)**: show that their martingale is the zero-drift boundary $p_1 = p^* = \kappa/(1+\kappa)$, whereas Proposition 3.3 captures nonzero drift when $p_1 \neq p^*$.
2. Verify that the **Overnight GPU Queue (Track A)** is running smoothly and has all tasks queued through 9:00 AM Saturday.
3. Run `pytest -q` and commit `reports/HOUR_06.md`.

---

## DAY 2: SATURDAY, NOV 14 (9:00 AM – 7:00 PM) — HARVEST OVERNIGHT RUNS, LAUNCH ROUTE III GPU JOB, LITERATURE & PACKAGE REFACTOR

### HOUR 7 (9:00 AM – 10:00 AM): Harvest Overnight GPU Logs, Launch Route III GPU Job & Update Bibliography
1. Inspect all overnight GPU outputs in `outputs/experiments/confirmatory/`.
2. **LAUNCH TRACK A GPU JOB 3 (Detached):** Start **Route III Heterogeneous Panel** (`llama3.1:8b` + `qwen2.5:7b` + `deepseek-r1:14b`: Homogeneous Voting vs. Homogeneous Debate vs. Heterogeneous Voting without chat vs. Heterogeneous Debate with chat) + **Hidden-Profile Dose–Response** ($0\%, 25\%, 50\%, 75\%, 100\%$ split evidence).
3. Update `manuscript/references.bib` and Section 2 / Section 3.4:
   - Fix `kapoor2024ai` to **`Transactions on Machine Learning Research (TMLR), 2025`**.
   - Add and cite **HiddenBench** (Li, Naito, & Shirado, ICML 2026), **Self-MoA** (Li et al., 2025, `arXiv:2502.00674`), **Chen et al. (NeurIPS 2024, `arXiv:2403.02419`)**, **Xu et al. (2026, `arXiv:2601.12307`)**, **Cemri et al. (2025, `arXiv:2503.13657`)**, and **Anthropic (2025)**.
4. Commit `reports/HOUR_07.md`.

### HOUR 8 (10:00 AM – 11:00 AM): Finalize Human Verification Sheets & 40-Question Editor Defense Guide (While GPU Job 3 Runs)
1. Verify Subagent C2's outputs (`review/hand_check.csv`, `review/crops/`, and `review/second_rater_sheet_blank.csv`) and test `scripts/audit_pipeline.py status`.
2. Write `reports/defense_questions.md` (40 technical questions an Action Editor could ask about every equation, baseline classification, and estimator in the paper).
3. Commit `reports/HOUR_08.md`.

### HOUR 9 (11:00 AM – 12:00 PM): Unify Python Package (`pace-eval` / `pace_eval`) & CLI Aliases (While GPU Job 3 Runs)
1. Update `code/pyproject.toml` so the distribution name is `pace-eval`, the primary import namespace is `pace_eval` (keeping `pace`, `cme`, and `mae_eval` as backward-compatible import aliases), and the CLI installs `pace-eval` and `pace` (with `cme` and `mae-eval` as deprecated aliases).
2. Test installing in editable mode and running all subcommands (`audit`, `classify`, `frontier`, `report`, `dynamics`, `hidden-profile`) with `pytest -q`. Do not publish to PyPI yet.
3. Commit `reports/HOUR_09.md`.

### HOUR 10 (12:00 PM – 1:00 PM): Process All Completed Live GPU Logs via `pace report` & `pace dynamics`
1. Run `pace report` and `pace dynamics` on the completed live JSONL logs from the overnight and morning runs.
2. Compute and save to `outputs/confirmatory_summary.json`:
   - Multi-axis frontier gaps ($\Delta_{\mathrm{frontier}}$ wrt total tokens, generation calls, wall-clock latency, and cost) + raw, isotonic, and cumulative-max voting curves + sample-equivalent $k^*$,
   - Empirical paired item correlation $\hat{\varphi}$,
   - Adjacent-round transition rates $(\hat{\tau}_{i\to c}, \hat{\tau}_{c\to i}, \hat{\kappa}, \hat{p}^*)$ + split-half out-of-sample accuracy predictions, and
   - Round-by-round $\hat{\rho}_{\mathrm{total}}$, $\Delta\hat{\rho}_{\mathrm{debate}}$, and $\hat{K}_{\mathrm{eff}}$ across homogeneous, heterogeneous, and verifier-gated runs.
3. Commit `reports/HOUR_10.md`.

### HOUR 11 (1:00 PM – 2:00 PM): Replace Synthetic Fixtures in Appendix D/D.1 & Overlay Real Points onto Figure 3
1. Place the verified real model JSONL traces in `code/pace/examples/` and update Appendix D and D.1 (`manuscript/appendix.tex`) so all CLI listings show real model runs (updating `tests/test_cme_audit.py` to match).
2. Update `analysis/plot_theory_phase_diagram.py` (**Figure 3**) to overlay the measured empirical $(\hat{K}_{\mathrm{eff}}, \hat{\rho}_{\mathrm{peer}})$ and $(\hat{\kappa}, p_1)$ points from the live runs alongside the theoretical curves.
3. Commit `reports/HOUR_11.md`.

### HOUR 12 (2:00 PM – 3:00 PM): Populate Section 6 (Controlled Validation of PACE & Escape Routes)
1. Populate `manuscript/module_confirmatory_results.tex` (and enable `INCLUDE_CONFIRMATORY=1` in `assemble_paper.py`) with a crisp, 2-page validation section reporting:
   - Table & frontier curves for the 6 core arms on shared-evidence reasoning (showing the frontier gap across tokens, calls, and latency),
   - The $2\times 2$ Hidden-Profile crossover and dose–response curve (Route I),
   - Verifier-gated debate vs. verifier-gated independent sampling (Route II), and
   - Heterogeneous debate vs. heterogeneous voting without communication (Route III) + split-half out-of-sample transition rate validation.
2. Commit `reports/HOUR_12.md`.

### HOURS 13–14 (3:00 PM – 5:00 PM): Tighten Main Text to 13–15 Pages & Run Claims Ledger Audit
1. **LAUNCH SUBAGENT C5 (Parallel Isolated Output):** Build `review/CLAIMS_LEDGER.csv` mapping every claim and number in the Abstract, Introduction, Sections 5–6, and Conclusion to its backing table/figure/proposition and flagging any number repeated $>2$ times.
2. Tighten the main text of `tmlr_submission.tex` and `main.tex` from 23 pages down to **13–15 pages** (before References) by moving detailed per-study narratives, secondary sensitivity tables, and full proofs cleanly to Appendices A–E while keeping the PACE methodology, the 9-study synthesis (Tables 1–3, Figures 1–5, 7–8), and the live validation (Section 6) front and center.
3. Commit `reports/HOUR_13_14.md`.

### HOURS 15–16 (5:00 PM – 7:00 PM): Full Build Gates, Visual Page Inspection & Clean-Clone Submission Archives
1. Run `analysis/assemble_paper.py`, `analysis/build_gates.py`, and `pytest -q`, verifying 100% pass rate, 0 LaTeX warnings, 0 undefined references (`??`), and 0 overfull `\hbox`es.
2. Render all pages of `manuscript/tmlr_submission.pdf` and `arxiv_version/main.pdf` to PNG (`pdftoppm -png -r 150`) and inspect every figure and table visually.
3. Build `supplementary_materials.zip` (for TMLR) and flat root-level `arxiv_submission.zip` (for `arXiv v2` with all macros inlined), test-compile both from scratch in a clean temporary directory, and write the final summary in `STATUS.md` and `reports/HOUR_15_16.md`.
