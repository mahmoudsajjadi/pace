# Phase 10: Constructive Validation, Empirical Calibration, and Community Rebuttal Suite

> **Context & Foundation (2026-11-12):**
> - **Preceding Baselines:** Commit `6b508fd` (Phase 2 harness, OSF preregistration draft, greedy pilot across 5 models, run manifest), `186a0b7` (Phased Roadmap), `6f49f3d` (10-item manuscript overhaul, CHE REML engine, 516 unique MAS configs / 531 raw rows), and `713c89c`.
> - **Two-Part Scientific Formula:** 
>   1. *Negative Audit (Confound Deconstruction):* 9-study empirical synthesis demonstrating that multi-agent systems average $-0.042$ ($\hat{\beta} = -0.195$, CR2 95% CI $[-0.320, -0.070]$) against sampled and budget-matched baselines.
>   2. *Constructive Positive Control:* 50-item Split-Evidence "Hidden Profile" benchmark demonstrating that when premises are partitioned across agents ($\mathcal{I}(Y; X_j \mid X_i) > 0$), independent majority voting (Category B) collapses to **0%** while multi-agent communication reaches **83%**.

---

## 1. Authoritative Statistical, Experimental, and Architectural Decisions

### A. Statistical & Meta-Analytic Architecture
1. **Table 3 Calibration Integration ($\varphi = 0.50$ vs. Empirical $\hat{\varphi}$):**
   - Retain $\varphi = 0.50$ as the primary pre-specified baseline row in Table 3.
   - Add one new validation row at the bottom of Table 3: `B9 (at empirical \hat{\varphi} from Phase 2 calibration)`, showing that the pooled Category B/C log-odds estimate and CR2 95% CI remain invariant when evaluated at the empirically measured paired-item correlation $\hat{\varphi}$.
   - Full calibration details presented in Section 5.4 and Appendix A.2.
2. **Cluster Degrees of Freedom ($\nu = 4.7$ to $7.2$) & Small-Sample Inference:**
   - Present `Wald 95% CI` ($z_{0.975} = 1.96$) and `CR2 95% CI` side by side in Table 3.
   - Clarify in the caption that the `CR2 95% CI` column incorporates Bell–McCaffrey (2002) / Tipton (2015) small-sample Student-$t$ critical values ($t_{\nu, 0.975}$, e.g. $t_{7.2, 0.975} = 2.350$).
   - Report exact two-sided small-sample $p_{\text{CR2}}$ ($t = -0.195 / 0.053 = -3.68 \implies p_{\text{CR2}} = 0.0074$), demonstrating significance at $p < 0.01$ under strict small-sample penalties.

### B. Experimental Design & Positive Control Validation
1. **DeepSeek-R1 `<think>` Token Accounting:**
   - Partition generation calls into three mutually exclusive buckets:
     - $R_{\text{reason}}$: Internal thinking tokens inside `<think>...</think>`.
     - $R_{\text{comm}}$: Visible post-`</think>` message tokens broadcast to peers.
     - $R_{\text{scaffold}}$: Input prompts, system instructions, and echoed history re-ingested across rounds ($R_{\text{token}} = R_{\text{reason}} + R_{\text{comm}} + R_{\text{scaffold}}$).
   - *Key Architectural Insight:* Reasoning-model chat templates strip `<think>` tokens across multi-turn handoffs, forcing communicating agents to exchange compressed summaries and discarding intermediate latent trajectories, whereas a single agent under Category C thinking-token parity maintains an unbroken reasoning trace.
2. **The Split-Evidence "Hidden Profile" Positive Control (`0%` Voting vs. `83%` Debate):**
   - Feature in the main text (Section 5.5 / 6.5) and formalize via Conditional Mutual Information:
     - *Redundant-Context Regime:* $\mathcal{I}(Y; X_j \mid X_i) = 0 \implies$ communication adds no new task information, incurring only scaffold overhead $\sum C_{\text{scaffold}}$.
     - *Complementary-Context ("Hidden Profile") Regime:* $\mathcal{I}(Y; X_j \mid X_i) > 0 \implies$ no individual partition determines $Y$ (independent voting scores **0%**), while joint premises determine $Y$ (communicating debate scores **83%**).
   - Package the benchmark in `mae-eval` as `mae-eval run-positive-control` to serve as a 2-minute Information Synthesis Efficiency test for new agent architectures.

### C. Community Tooling Architecture
1. **Automatic Baseline Ladder Classifier (`mae_eval/classifier.py`):**
   - Implement `classify_baseline_rung(sas_metrics, mas_metrics, eps=0.10)`:
     - *Category D (Pareto):* $\ge 3$ budget levels tracing accuracy vs. cost/tokens.
     - *Category C (Budget-Matched):* Relative deviation $\le 10\%$ on $R_{\text{reason}}, R_{\text{token}}, R_{\text{cost}},$ or $R_{\text{lat}}$.
     - *Category B (Sample-Matched):* $R_{\text{sample}} \ge 2$ with matched samples or CoT-SC.
     - *Category A (Greedy Single-Pass):* $R_{\text{sample}} = 1$ and token expansion $> 1.10\times$ (emits warning flag).
     - *Dual-Baseline Check:* Automatically logs $\Delta_{\text{gap}} = \Delta_{\text{Cat B}} - \Delta_{\text{Cat A}}$.
2. **Rebuttal Table Generator (`mae-eval report --export-latex` and `--export-markdown`):**
   - 9 reviewer-requested columns: `System / Rung`, `Acc (%) ± 95% CI`, `Δ vs Cat A`, `Δ vs Cat B/C`, `Sampling Gap (Δ_gap)`, `McNemar p-val (and \hat{\varphi})`, `Tokens (R_reason / R_token / Scaffold %)`, `Cost & Latency Ratio`, and `CME Parity Status`.

---

## 2. Phase 10 Master Execution Prompt for Claude Code

```markdown
Phase 10: Integrating Empirical Calibration (`deepseek-r1:14b`), the Split-Evidence "Hidden Profile" Positive Control (0% vs. 83%), and the Automated Rebuttal/Classifier Suite
Project: C:\Users\17756\OneDrive - University of Nevada, Reno\Projects\Automation\01_Research\Manuscripts\01_pure_ml_reasoning_and_test_time_compute

Execute the following 5 tasks from `docs/PHASE10_CONSTRUCTIVE_VALIDATION_AND_REBUTTAL_SPEC.md`:

### TASK 1: Integrate Empirical Item Correlation (\hat{\varphi}) and Small-Sample CR2 t_\nu p-Values in Table 3
1. In Table 3 (Section 5.4) and Table 4 (Appendix A.2), retain $\varphi = 0.50$ as the primary pre-specified baseline row, and add a new validation row at the bottom of Table 3:
   `B9 (at empirical \hat{\varphi} from Phase 2 calibration)` showing that the pooled Category B/C log-odds estimate and CR2 95% CI remain invariant when using the empirically measured paired-item correlation $\hat{\varphi}$.
2. Add a `CR2 p-val` column (or report the exact two-sided small-sample $p_{\text{CR2}}$ from the Bell–McCaffrey / Tipton $t_\nu$ distribution) in Table 3, explicitly noting in the Table 3 caption that CR2 95% confidence intervals use exact Satterthwaite $t_{\nu, 0.975}$ critical values rather than normal $z$-approximations.

### TASK 2: Formalize `<think>` Token Disentanglement & the Split-Evidence "Hidden Profile" Positive Control
1. **DeepSeek-R1 `<think>` Token Accounting**:
   - In Section 4 / Section 5 (and `code/mae_eval/`), formalize the three-way token split for reasoning models emitting `<think>...</think>`: internal thinking tokens ($R_{\text{reason}}$), visible peer-broadcast tokens ($R_{\text{comm}}$), and prompt/echoed-history scaffold tokens ($R_{\text{scaffold}}$), where $R_{\text{token}} = R_{\text{reason}} + R_{\text{comm}} + R_{\text{scaffold}}$.
   - Highlight the architectural insight that multi-turn chat templates strip `<think>` blocks across rounds—forcing communicating agents to pass compressed post-`</think>` summaries—whereas a single agent under Category C thinking-token parity retains an unbroken internal reasoning chain.
2. **The Split-Evidence "Hidden Profile" Positive Control (`0%` Voting vs. `83%` Debate)**:
   - Add a concise subsection in the main text (and full specification in `docs/BENCHMARK_SPECIFICATION.md`) presenting our 50-item Split-Evidence "Hidden Profile" validation experiment alongside the 200-item standard benchmark calibration.
   - Frame the contrast via Conditional Mutual Information: on standard shared-context benchmarks ($\mathcal{I}(Y; X_j \mid X_i) = 0$), multi-agent debate fails to beat Category B voting/Category C single-agent thinking; conversely, on the Split-Evidence Hidden Profile task where premises are partitioned across agents ($\mathcal{I}(Y; X_j \mid X_i) > 0$), Category B independent voting scores `0%` while multi-agent debate reaches `83%`. This provides a constructive litmus test proving that our CME framework accurately detects true coordination when task structure requires distributed information synthesis (confirming Rule 2 in Section 7.2).

### TASK 3: Implement the Automatic Baseline Ladder Classifier & OpenReview Rebuttal Exporter in `mae-eval`
1. **Automatic Classifier (`mae_eval/classifier.py`)**:
   - Implement `classify_baseline_rung(sas_metrics, mas_metrics, eps=0.10)` applying our 5-rule decision tree (`Category D` Pareto sweep $\ge 3$ budgets; `Category C` resource match within $\pm 10\%$ on $R_{\text{reason}}, R_{\text{token}}, R_{\text{cost}},$ or $R_{\text{lat}}$; `Category B` sample match $R_{\text{sample}} \ge 2$; `Category A` single greedy pass $R_{\text{sample}} = 1$) and wire it into `ADD_YOUR_STUDY.md` validation.
2. **Rebuttal Table Generator (`mae-eval report --export-latex` & `--export-markdown`)**:
   - Output the 9 reviewer-requested columns: `System / Rung`, `Acc (%) ± 95% CI`, `Δ vs Cat A`, `Δ vs Cat B/C`, `Sampling Gap (Δ_gap)`, `McNemar p-val (and empirical \hat{\varphi})`, `Tokens (R_reason / R_token / Scaffold %)`, `Cost & Latency Ratio`, and `CME Parity Status`, with the citation to our paper pre-embedded in the table note.
   - Update Appendix D (Page 27–28) to display the real calibration trace and `--export-latex` / `--export-markdown` output instead of the synthetic hand-written placeholder trace.

### TASK 4: Fix the Remaining Visual Glitches from `tmlr_submission_2.pdf`
1. Update the subtitle to `Untangling Coordination, Ensembling, and Test-Time Compute in Multi-Agent LLMs` (eliminating the "Samples / Sampling" word repetition) and remove the redundant `*` footnote from the main title on Page 1.
2. Fix Figure 7's log-scale minor tick overlap (`NullLocator()`/`NullFormatter()`), Figure 4's bottom footer line clipping, Figure 2's right label padding, and Equation (4)'s `\mathcal{B}_0 < \mathcal{B}_A` notation.
3. Add the 2-Panel REML & Sensitivity Forest Plot (`figures/fig_reml_forest_plot.pdf`) visualizing Table 3 and Table 4.

### TASK 5: Run Full Test Suite & Visual PNG Inspection
1. Run `pytest` across all unit and integration tests and verify 100% pass rate.
2. Recompile `tmlr_submission.pdf` and `main.pdf` with 0 errors, 0 undefined references, and 0 overfull boxes, and visually inspect the rendered PNG pages.
```
