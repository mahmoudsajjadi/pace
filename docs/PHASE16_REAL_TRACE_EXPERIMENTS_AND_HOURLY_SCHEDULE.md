# Phase 16: Real LLM Trace Experiments, Excess Debate Correlation, Cached Figure Audit, and Hourly Execution Schedule (6:00 PM Onward)

> **Policy & Guardrail Reconciliation Note:**
> - **TMLR Page-1 AI Footnote (`G-THANKS` / `G-VERIF`):** Keep the Page-1 `\thanks{AI tools ...}` footnote intact per TMLR FAQ and `analysis/build_gates.py`.
> - **Truthful Hand-Inspection Provenance:** Do NOT remove the hand-inspection note until the human author signs `review/HAND_VERIFICATION_CHECKLIST.md`.
> - **GPU / Confirmatory Queue Protection:** `outputs/experiments/confirmatory/llama3.1-8b__hidden_profile/` and the armed `queue_deepseek.lock` have priority on local Ollama VRAM. Any new local LLM run must either wait for the queue or use an isolated API/non-conflicting slot.

---

## 1. Non-Experimental Fixes & Diagnostics Remaining from `tmlr_submission_6.pdf`

1. **Audit & Overwrite Cached Figure Paths (`Figure 4`, `Figure 8`, `Figure 9`):**
   - Verify exact `\includegraphics` paths in `manuscript/` and `paper/` (`figures/`, `manuscript/figures/`, `paper/figures/`).
   - **Figure 4 (Resource Matrix):** Ensure left `"J"` in `"Jwalapuram et al. (2026)"` has generous padding (`pad_inches=0.35`) across all target directories.
   - **Figure 8 (REML Forest Plot):** Ensure left `"K"` in `"Ke (m = 29)"` and `"J"` in `"Jwalapuram (m = 107)"` are never clipped on Panel A's y-axis.
   - **Figure 9 (Tran & Kiela Scaling Curves):** Delete any stale cached PDF/PNG across `figures/`, `manuscript/figures/`, `paper/figures/`, regenerate with `NullLocator()`/`NullFormatter()` applied *after* `set_xscale('log')`, and visually verify rendered PNG ticks read cleanly `100, 500, 1k, 2k, 5k, 10k`.
2. **Excess Debate Correlation in `cme dynamics`:**
   - Report both raw pairwise correlation across items ($\hat{\rho}_{\mathrm{total}}$, including shared item difficulty) AND the **excess correlation induced by debate** ($\Delta\hat{\rho}_{\mathrm{debate}} = \hat{\rho}_{\mathrm{peer}}^{(T)} - \hat{\rho}_{\mathrm{peer}}^{(1)}$) so reviewers see how debate elevates inter-agent correlation above Round 1.
3. **Human Author Sign-Off (Pending Author Action):**
   - Visually inspect the 9 source PDF tables and sign `review/HAND_VERIFICATION_CHECKLIST.md`. Once signed, update the 4 `VERIF` locations truthfully.

---

## 2. The 3 Targeted Validation Experiments (Replacing `"synthetic": true` Traces)

### Experiment 1: Real Debate Transcript Dynamics ($\hat{\rho}_{\mathrm{peer}}, \Delta\hat{\rho}_{\mathrm{debate}}, \hat{K}_{\mathrm{eff}}, \hat{\tau}_{i\to c}, \hat{\tau}_{c\to i}, \hat{\kappa}, \hat{p}^*, \hat{\varphi}$)
- **Models:** `Qwen2.5-7B-Instruct` and `Llama-3.1-8B-Instruct` (matching Choi et al., 2025) + one reasoning model (`DeepSeek-R1-Distill-Qwen-14B` or API tier).
- **Benchmarks ($N = 100$ items each):**
  1. *High-Baseline Regime ($p_1 > 0.45$):* `GSM8K` ($N=100$).
  2. *Low-Baseline Regime ($p_1 < 0.45$):* `GPQA-Diamond` or `MATH-Level-5` ($N=100$).
- **Arms:** Cat. A (Greedy $K=1$), Cat. B ($K=5$ CoT-SC, $T=0.7$), Cat. C (Token-Matched Single Agent), MAS Debate ($K=5, T=3$).
- **Measurements (`cme dynamics` + `cme report`):** Round 1 vs. Round 3 $\hat{\rho}_{\mathrm{peer}}$ and $\hat{K}_{\mathrm{eff}}$, $\Delta\hat{\rho}_{\mathrm{debate}}$, transition rates $(\hat{\tau}_{i\to c}, \hat{\tau}_{c\to i}, \hat{\kappa}, \hat{p}^*)$, and empirical paired item correlation $\hat{\varphi}$.

### Experiment 2: Stasser & Titus (1985) Hidden-Profile 2×2 Design (Proposition 3.1 & Route I)
- **Setup ($N = 100$ items from `hp.jsonl`, $K=5$ agents):**
  - *Split / Hidden-Profile Evidence* ($\mathcal{I}_{\mathrm{part}} > 0$) vs. *Shared / Redundant Evidence* ($\mathcal{I}_{\mathrm{part}} = 0$).
  - Crossed with *Cat. B Independent Voting ($T=1$)* vs. *Multi-Agent Debate ($T=2$ rounds)*.

### Experiment 3: Route II (External Verifier Gating) & Route III (Cross-Model Error Decorrelation)
- **Route II ($R_{\mathrm{sys}} > 0$):** 5-agent debate gated by deterministic Python/unit-test check ($V \in R_{\mathrm{sys}}$); measure drop in $\hat{\tau}_{c\to i}$ and rise in $\hat{\kappa}, \hat{p}^*$.
- **Route III:** Compare Homogeneous Panel (3× `Qwen2.5-7B`) vs. Heterogeneous Panel (`Qwen2.5-7B` + `Llama-3.1-8B` + `Mistral-7B`/`Gemma-2-9B`) under Voting vs. Debate; measure $\hat{\rho}_{\mathrm{het}} < \hat{\rho}_{\mathrm{hom}}$ and gain in $\hat{K}_{\mathrm{eff}}$.

---

## 3. Hourly Execution Schedule (Starting 6:00 PM, 1-Hour Increments)

- **Hour 1 (6:00 PM – 7:00 PM): Cached Figures, `cme dynamics` Excess Correlation, & Environment Check**
  - Verify/fix exact `\includegraphics` paths for Figures 4, 8, and 9 across all 3 figure folders; inspect rendered PNGs.
  - Add $\Delta\hat{\rho}_{\mathrm{debate}} = \hat{\rho}_{\mathrm{peer}}^{(T)} - \hat{\rho}_{\mathrm{peer}}^{(1)}$ to `code/cme/dynamics.py` + unit tests.
  - Inspect running `outputs/experiments/confirmatory/` GPU usage and verify whether `llama3.1:8b` / `deepseek-r1:14b` queue is still active.
- **Hour 2 (7:00 PM – 8:00 PM): Queue / Launch Experiment 2 (Hidden-Profile 2×2) & Route II Verifier Harness**
  - Configure `cme` experiment runner for Experiment 2 (Hidden Profile 2×2, $N=100$) and Experiment 3 Route II (Python verifier gating).
  - Queue sequentially behind active confirmatory runs (or execute immediately if GPU is free / API key configured).
- **Hour 3 (8:00 PM – 9:00 PM): Queue / Launch Experiment 1 (GSM8K & MATH-L5/GPQA Debate Dynamics) & Route III Heterogeneous Panel**
  - Launch Experiment 1 ($K=5, T=3$ debate + Cat. A/B/C arms) and Route III cross-model panel.
- **Hour 4 (9:00 PM – 10:00 PM): Run `cme dynamics` & `cme report` on Completed Real Traces + Plot Empirical Points on Figure 3**
  - Process completed real JSONL traces via `cme dynamics` and `cme report`.
  - Overlay real empirical $(\hat{K}_{\mathrm{eff}}, \hat{\rho}_{\mathrm{peer}})$ and $(\hat{\kappa}, p_1)$ points onto Figure 3A and 3B.
- **Hour 5 (10:00 PM – 11:00 PM): Manuscript Integration, Appendix D Replacement, & Full Verification**
  - Update Appendix D/D.1 with real executed model traces (removing `"synthetic": true` disclaimers only for traces backed by real logged runs), update Section 5.5 summary table, run `pytest -q`, recompile via `assemble_paper.py`, inspect all rendered PNGs, and commit locally.
