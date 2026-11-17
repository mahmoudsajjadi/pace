# Acceptance, Citation, Denominator, and Methodological Bulletproofing Reference (2026–2035)

This reference integrates two external methodological and editorial reviews (originally evaluated against earlier 52-page snapshots `tmlr_submission_3.pdf` / `tmlr_submission(4).pdf` prior to Section 6 activation and Appendix relocations) into the live Phase 16 PACE manuscript state.

---

## Part 1: Venue Acceptance Forecast Matrix

Editorial probability ranges compare earlier 52-page snapshots (before Section 6 controlled experiments, redrawn vector figures, and main-text tightening to page 27 before References) against the upgraded Phase 16 live manuscript (`manuscript/tmlr_submission.pdf`, `INCLUDE_CONFIRMATORY=1`). These are editorial judgments, not calibrated predictions.

| Venue / Track | Review 1 Estimate (`tmlr_submission(4).pdf`) | Review 2 Estimate (`tmlr_submission_3.pdf`) | Primary Decision Drivers & Live Phase 16 Improvements |
|---|---|---|---|
| **TMLR — Standard Acceptance** | 30–45% | 93–96% | Strong scope fit (`Parity-Aware Compute Evaluation`, directional feasibility, MMLU-Pro + Hidden Profile controlled experiment now in Section 6, redrawn Figures 1/2/4/5/10, References brought to p. 28). Remaining core risk: Page-1/Section-5/Open-Science human-verification disclosure (`AI tools extracted...`). |
| **TMLR — J2C Certification (conditional)** | 5–10% | 28–38% (Featured / J2C) | Conditional on acceptance (~10% selective bar); boosted by controlled experiment + operational per-item schema/card/rules, constrained by non-manual table re-reading disclosure. |
| **TMLR — Featured / Outstanding** | 3–8% (Featured) / 1–3% (Outstanding) | — | Requires strong AE/reviewer consensus that PACE is reusable default infrastructure. |
| **NeurIPS Evaluations & Datasets Track** | 25–40% | 78–86% | Close thematic match to evaluation protocols, negative results, auditing practices, 516-configuration / 834-record corpus, and `pace` utilities (do not dual-submit while under TMLR review). |
| **NeurIPS / ICML / ICLR Main Track** | 10–22% | 42–52% (as-is) -> 76–84% (with 9–10p restructuring + live traces) | Main tracks enforce 9–10 page bodies and penalize purely methodological audits without condensed live empirical traces in body. |
| **JMLR** | 10–20% | 72–80% | Fits theoretical rigor (Blackwell, Manski, Kish, Krogh–Vedelsby), but >50p requires cover-letter justification and signed human audit of extraction rows. |

---

## Part 2: Citation Forecasts (2026–2035) and Adoption Engine

### 2.1 Conservative Scenario Model (Review 1, Conditional on Publication)

| Year | Trajectory 1: Published as Critique + Protocol | Trajectory 2: Bulletproofed Paper + Reusable Workflow | Trajectory 3: Institutional Venue Adoption (Counterfactual) |
|---|---|---|---|
| 2026 | 0 | 0 | 0 |
| 2027 | 3 | 6 | 10 |
| 2028 | 8 | 20 | 40 |
| 2029 | 15 | 45 | 120 |
| 2030 | 24 | 80 | 250 |
| 2031 | 34 | 125 | 450 |
| 2032 | 45 | 180 | 700 |
| 2033 | 55 | 245 | 950 |
| 2034 | 65 | 320 | 1,200 |
| 2035 | 75 | 400 | 1,500 |
| **10-Year Total** | **324** | **1,421** | **5,220** |

### 2.2 Compounding Infrastructure Model (Review 2, Annual / Cumulative)

| Year | Scenario A: Baseline As-Is | Scenario B: With Prose, Visual & Structural Upgrades | Scenario C: Default Harness & Rebuttal Standard |
|---|---|---|---|
| 2026 | 4 / 4 | 8 / 8 | 15 / 15 |
| 2027 | 38 / 42 | 75 / 83 | 160 / 175 |
| 2028 | 95 / 137 | 190 / 273 | 480 / 655 |
| 2029 | 155 / 292 | 310 / 583 | 960 / 1,615 |
| 2030 | 180 / 472 | 360 / 943 | 1,420 / 3,035 |
| 2031 | 165 / 637 | 340 / 1,283 | 1,650 / 4,685 |
| 2032 | 140 / 777 | 295 / 1,578 | 1,600 / 6,285 |
| 2033 | 120 / 897 | 255 / 1,833 | 1,450 / 7,735 |
| 2034 | 100 / 997 | 220 / 2,053 | 1,280 / 9,015 |
| 2035 | 85 / **1,082** | 190 / **2,243** | 1,135 / **10,150** |

**Adoption identity:** If $N$ relevant papers appear annually, $a$ is the adopting fraction, and $c$ is the citation fraction among adopters, direct annual protocol citations scale as $C_{\mathrm{annual}} \approx N a c$.

### 2.3 Landmark Gap Matrix

| Reference Paper | Reusable Contribution | Phase 16 PACE Alignment |
|---|---|---|
| Henderson et al. (2018), *Deep RL That Matters* | Concrete seed/reproducibility standards reviewers cite and enforce | Highlight zero-cost nested initial-round voting (`PACE-Minimum`) & directional feasibility |
| Liang et al. (2022), *HELM* | Standardized multi-scenario evaluation matrix & shared artifacts | Synchronize `"Sampled"` naming across tables/figures + factual captions (Rule C.5) |
| Wang et al. (2023), *Self-Consistency* | Concrete algorithmic baseline + symbol reused across Methods sections | Spotlight $k_{\mathrm{tok}}$ pool sizing & $\mathbf{R}$ vector + 7-row Evaluation Card |
| Snell et al. (2024), *Scaling Test-Time Compute* | Explicit compute scaling variables & budget allocation frontiers | Pair $\mathbf{R}$ accounting with equal-token frontier curves (`fig:controlled_frontier`) |
| Dietterich (2000) & Krogh–Vedelsby (1994) | Three-reason positive checklist (statistical/computational/representational) + ensemble covariance | Frame Routes I–III + parallel state + placebo/verifier objectives so builders and critics alike cite PACE |
| Bouthillier et al. (2021) | Summary table first, walking readers through units cleanly | Three-unit signpost at top of Section 5.3 + Four-Case diagnostic synthesis in Section 7.1 |

---

## Part 3: Canonical Denominator Ledger (Exact Reconciled Counts)

Never conflate comparison records, unique MAS configurations, linked pairs, deduplicated baseline cells, or sensitivity family clusters:

| Analytical Unit | Exact Count | Provenance / Decomposition |
|---|---|---|
| Papers considered across two stages | **12** | 5 initial studies spanning resource dimensions + 7 candidate papers screened in Appendix C.1 (not all 12 underwent the same formal screen). |
| Included / Excluded studies | **9** included / **3** excluded | 5 initial + 4 eligible candidates (Ke 2026, Yang 2025, Zhang 2025, Smit 2024). |
| Raw extracted table rows | **531** | 252 from initial 5 studies + 279 from 4 added studies. |
| Excluded baseline-only rows | **15** | 14 majority-voting rows in Choi et al. + 1 self-consistency row in Wunderlich et al. (NOT duplicate rows in Tran & Kiela). |
| **Unique MAS configurations** | **516** | $531 - 15 = 516$ ($237 + 279$). |
| Category A comparison records | **358** | MAS vs. single greedy pass across 5 studies. |
| Category B comparison records | **360** | MAS vs. sampled baseline across 6 studies. |
| Category C comparison records | **114** | MAS vs. budget-matched / shared-ceiling baseline across 2 studies (`Tran` 96 + `Kim` 18). |
| Category D Pareto comparisons | **2** | `Wunderlich` Debate & MoA vs. SC at comparable compute on Pareto fronts. |
| **Combined Category B/C pool** | **474** | $360 + 114 = 474$ across 8 studies (`B9` REML & `tab:baseline_tiers`). |
| Arithmetic sum of A/B/C/D comparison records | **834** | $358 + 360 + 114 + 2 = 834$ baseline-specific comparison records (overlapping when a source compares one MAS arm to multiple baselines; NOT 834 independent experiments). |
| Shared-ceiling / matched-generation slice | **156** | 96 Tran thinking-token contrasts + 18 Kim iteration contrasts + 42 Yang generation-matched contrasts. |
| **Linked Category A/B sampling-gap pairs** | **318** | $107\text{ (Jwalapuram)} + 140\text{ (Zhang)} + 28\text{ (Smit)} + 29\text{ (Ke)} + 14\text{ (Choi)} = 318$ (281 negative, 88%). Do NOT write 358 for sampling-gap pairs. |
| **Deduplicated baseline cells (`D_cells`)** | **72** | Unique $(\mathrm{study}, \mathrm{benchmark}, \mathrm{model})$ baseline cells collapsing the 318 pairs (64 of 72 negative, 89%; $\hat\beta = -0.178$, CR2 95% CI $[-0.333, -0.022]$). |
| Normalized framework-family clusters | **19** | Sensitivity clustering taxonomy in Section 5.4 / Appendix A.2 (merged SoM into MAD/Deb/SoM); distinct from the **5 topology archetypes** in Table B.7. |

---

## Part 4: Mathematical & Methodological Guardrails

1. **Keep Existing Title & Acronym:** *PACE: Parity-Aware Compute Evaluation* (do NOT rename to *Protocol-Anchored Compute Equivalence*).
2. **Preserve Exact Conformity Drift Sign (Proposition 3.3 Check):**
   - For $p_{01} = \Pr(0 \to 1)$ and $p_{10} = \Pr(1 \to 0)$, expected change is $\Delta p = (1 - p_1)p_{01} - p_1 p_{10}$.
   - Positive expected drift requires:
     $$p_{01} > \frac{p_1}{1 - p_1} p_{10}$$
     which matches Proposition 3.3 ($\kappa > p_1/(1-p_1)$). Never invert the multiplier to $(1-p_1)/p_1$.
3. **Avoid Undefined Quantities (`c_1 > c_2`):** Use the paper's conditional mutual information necessity condition $\operatorname{I}(Y; X_j \mid X_{\mathrm{shared}}, X_i) > 0$.
4. **Constructive Design Objectives (Clearly Labeled as Untested Future Protocol Objectives):**
   - **Placebo Overhead Decomposition:** $\Delta_{\mathrm{arch}} = p_{\mathrm{comm}} - p_{\mathrm{placebo}}$, $\Delta_{\mathrm{overhead}} = p_{\mathrm{full}} - p_{\mathrm{placebo}}$, yielding $p_{\mathrm{comm}} - p_{\mathrm{full}} = \Delta_{\mathrm{arch}} - \Delta_{\mathrm{overhead}}$; net gain requires $\Delta_{\mathrm{arch}} > \Delta_{\mathrm{overhead}}$ with volume-, schedule-, and tool-matched placebos.
   - **Verifier vs. Aggregation Transition Drift:** Compare $\Delta p_{\mathrm{ver}} = (1-p_1)\tau_{i\to c}^{\mathrm{ver}} - p_1\tau_{c\to i}^{\mathrm{ver}}$ against $\Delta p_{\mathrm{agg}} = (1-p_1)\tau_{i\to c}^{\mathrm{agg}} - p_1\tau_{c\to i}^{\mathrm{agg}}$ ($\Delta p_{\mathrm{ver}} > \Delta p_{\mathrm{agg}}$) rather than checking wrong-to-right alone.
   - **Cost Objective:** $\Delta C = C_{\mathrm{MAS}} - C_{\mathrm{baseline}} < 0$ is an expenditure metric requiring co-reporting with accuracy and remaining components of $\mathbf{R}$.
   - **Untested Fourth Structural Candidate:** Parallel tools and separated execution state (requires noncommunicating comparator with equivalent permissions, state-reset policy, and resource ceilings).
5. **Operational Protocol Rules for Modern Agent Traces (7th Field on Evaluation Card):**
   - **Per-Item Budget Matching ($k_i$):** Grow the sampled pool per item until matching realized MAS item expenditure $B_i^{\mathrm{MAS}}$, distinguishing itemwise dominance from matching in expectation.
   - **Adaptive Stopping:** Log stopping rule, declared ceiling, realized item distributions, and termination reason.
   - **Cache-Adjusted Billing-Equivalent Tokens:** Optional $C_{\mathrm{tok}}^{\mathrm{adj}}(\boldsymbol{\alpha}) = C_{\mathrm{in,uncached}} + \alpha_{\mathrm{cache}}C_{\mathrm{in,cached}} + \alpha_{\mathrm{out}}C_{\mathrm{out}}$ alongside raw $R_{\mathrm{token}}$ and $R_{\mathrm{cost}}$.
   - **Hybrid Policy Classification:** Directed call-graph trace classification ($\Pi_{\mathrm{agent}}$ whenever any model call reads an output from another thread), reporting counts of independent trajectories, self-continuation edges, cross-thread edges, model aggregation calls, judge calls, and external tool calls.
6. **External Validation Item Requiring Author Action Outside Manuscript Editing:**
   - Independent second human rater search of declared venues/dates and full independent human re-extraction of high-leverage table values (AI-use disclosures remain verbatim until independently executed and signed by the author).
