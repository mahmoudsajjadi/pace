# Phase 17 Plan: TMLR Certifications, `arXiv v2` Upgrades, and Ecosystem Adoption

**Target:** Secure **TMLR Featured Certification** (unlocking the Journal-to-Conference track at ICLR/ICML/NeurIPS), **Survey Certification**, and **Reproducibility Certification**, while preparing `arXiv v2` and community adoption multipliers.

---

## 1. Unified Venue & Certification Assessment (Reconciled)

| Target Venue or Outcome | Current (`arXiv v1`) | After Phase 17 (`v2`) | Primary Bottleneck to Resolve |
| --- | --- | --- | --- |
| **TMLR (Standard Acceptance)** | 88%--92% | 95%--97% | Minor typos & unverified per-contrast Pareto check |
| **TMLR Survey Certification** | 40%--55% | 70%--80% | Needs registered PRISMA search funnel & dual screening |
| **TMLR Reproducibility Certification** | 35%--50% | 75%--85% | Needs real LLM traces in Appendix D.1 & 1-command `Makefile` |
| **TMLR Featured Certification (J2C Track)** | 15%--25% | 35%--50% | Needs live LLM calibration + Hidden-Profile $2\times 2$ runs (note: TMLR expects ~10% of accepted papers to receive J2C) |
| **NeurIPS Datasets & Benchmarks Track** | 45%--55% | 65%--75% | Needs live Hidden-Profile benchmark baselines & HF dataset |
| **ACL / EMNLP Findings** | 55%--65% | 70%--80% | Needs trim from ~20 main-text pages to concise track format |
| **JAIR / ACM Computing Surveys** | 65%--75% | 80%--88% | Needs PRISMA search expansion & `Heter-MAD` extraction |
| **ICML / NeurIPS / ICLR Main Track** | 25%--35% | 45%--55% | Main-track reviewers expect primary multi-model experiments |

> [!NOTE]
> **Already Built in Repo:** `docs/PREREGISTRATION_PRISMA_REVIEW.md` (Section 11 OSF form text), `scripts/prisma_search.py`, `scripts/screen_literature.py`, `scripts/audit_pipeline.py`, `analysis/meta_regression.py`, and `analysis/run_moderator_tost.py` are already implemented. See [PHASE18_STRATEGIC_AUDIT_AND_ROADMAP.md](PHASE18_STRATEGIC_AUDIT_AND_ROADMAP.md) for the full strategic mission, senior-reviewer critique, and 2026--2035 roadmap.

---

## 2. How TMLR Certifications Unlock ICLR, ICML, and NeurIPS (J2C Track)

| TMLR Certification | What It Unlocks | Current Blocker | Exact Fix Required |
| --- | --- | --- | --- |
| **Featured Certification** | **J2C Track Invitation** to present at ICLR, ICML, or NeurIPS | No live LLM runs; Figure 3 and Appendix D.1 use simulated fixtures | Run the 3-part live LLM calibration & hidden-profile suite ($N=200$) |
| **Survey Certification** | Permanent badge + indexed as canonical field synthesis | Section 5.1 & 5.7 state initial 5 studies had no search protocol | Execute a reproducible API PRISMA search funnel in Figure 5 & Appendix C.1 |
| **Reproducibility Cert.** | Assigned reviewer verifies code & data from scratch | Appendix D.1 runs `pace` on synthetic coin-flip JSONLs (`tau_ic=0.30`) | Bundle real LLM JSONL traces + a 1-command `Makefile` / `pip install pace-eval` |

---

## 3. Phase 17 Execution Tasks (For `arXiv v2` & TMLR Submission)

### Task 1: Fix 4 Minor Typographic Glitches in `main.tex` & Figure 4
1. **Table 1, Row 2 (Page 14):** Fix double period `Kim et al..` -> `Kim et al.`
2. **Section 6.3, PACE Checklist Item 5 (Page 23):** Fix `"Does the paper per characterize task decomposability"` -> `"Does the paper characterize task decomposability"`.
3. **Appendix A.3 (Page 33):** Fix the two missing closing brackets in `$\varphi \in [0.00, 0.90$` -> `$\varphi \in [0.00, 0.90]$` and double period `Category B/C..` -> `Category B/C.`.
4. **Figure 4 (`fig2_resource_accounting_matrix.pdf`, Page 12):** Increase left padding (`bbox_inches='tight', pad_inches=0.35`) so the capital `"J"` in `"Jwalapuram et al. (2026)"` has clean whitespace to its left.

### Task 2: Solve Bottleneck 4 — Contrast-by-Contrast Pareto Dominance & `Heter-MAD`
1. **Verify Contrast-Level Resource Dominance Across All 474 Category B/C Contrasts (Section 5.3, Page 17):**
   - In `analysis/run_baseline_tiers.py`, audit each of the 474 Category B/C contrasts (and the 352 contrasts where $p_{\mathrm{MAS}} \le p_{\mathrm{SAS}}$) to check whether the single-agent baseline uses no more of the controlled/measured resources in $\mathbf{R}$ than the multi-agent system (noting where Jwalapuram et al. cost ratios are $< 1.0$ vs. $\ge 1.0$).
   - Replace *"We did not check the resource condition contrast by contrast..."* on Page 17 with the exact verified count/percentage of contrasts where the baseline strictly Pareto-dominates the multi-agent system on all measured dimensions of $\mathbf{R}$.
2. **Extract Zhang et al. Table 4 (`Heter-MAD`) into Appendix B.4:**
   - Extract the heterogeneous-model debate contrasts (`Heter-MAD`, Table 4 of Zhang et al.) against both greedy CoT and Self-Consistency.
   - Add **Appendix B.4 (Homogeneous vs. Heterogeneous Debate in Zhang et al.)** with a summary table comparing homogeneous vs. heterogeneous debate deltas, and update Table 10 (Page 38) to reference Appendix B.4.

### Task 3: Solve Bottleneck 2 — Formal PRISMA-2020 Programmatic Literature Search
1. Create `analysis/run_prisma_search.py` querying OpenAlex, Semantic Scholar, and arXiv (2023–2026) with an explicit Boolean query:
   ```text
   ("multi-agent debate" OR "multi-agent collaboration" OR "mixture of agents" OR "multi-agent reasoning")
   AND ("self-consistency" OR "majority voting" OR "compute budget" OR "token budget" OR "test-time compute")
   ```
2. Record the exact PRISMA-2020 identification, screening, eligibility, and inclusion counts in **Figure 5 (`fig_evidence_flow.pdf`, Page 13)** and **Appendix C.1 (Page 37)**, removing the self-limiting phrase *"chosen without a systematic search protocol"* in Sections 5.1 and 5.7.

### Task 4: Solve Bottlenecks 1 & 3 — Live LLM Calibration & Positive-Control Suite
Run three compact live experiments (local `Ollama` / `vLLM` or $<\$15$ API calls) and log every call in native `pace` JSONL format:
1. **Experiment A — Live Debate Dynamics & Item Correlation (`GSM8K` $N=100$ & `MATH-500` Level 5 / `GPQA-Diamond` $N=100$):**
   - **Models:** `Llama-3.1-8B-Instruct`, `Qwen2.5-7B-Instruct`, and `DeepSeek-R1-Distill-Qwen-14B` (separating `<think>` tokens $R_{\mathrm{reason}}$ from $R_{\mathrm{token}}$).
   - **4 Controlled Arms:** Category A (Greedy $K=1, T=1$), Category B ($k=5$ Majority Vote, $T=1$), Category C (Token-Matched Single Agent), and Multi-Agent Debate ($K=5, T=3$).
   - **Outputs:** Empirical item correlation $\hat{\varphi}$ (validation row in Table 3), round-by-round $\hat{\rho}_{\mathrm{peer}}^{(t)}$ and $\hat{K}_{\mathrm{eff}}^{(t)}$ (plotted onto Figure 3A), transition rates $\hat{\tau}_{i\to c}, \hat{\tau}_{c\to i}, \hat{\kappa}, \hat{p}^*$ (plotted onto Figure 3B), and real CLI traces in Appendix D.1.
2. **Experiment B — Stasser & Titus (1985) Hidden-Profile $2 \times 2$ Test (`hp.jsonl`, $N=100$, $K=5$ agents):**
   - Evaluate `Llama-3.1-8B-Instruct` and `Qwen2.5-7B-Instruct` under (Shared Prompt vs. Split Hidden-Profile Prompt) $\times$ (Category B Voting $T=1$ vs. Multi-Agent Debate $T=2$), tabulating the empirical crossover (Voting $\approx 0\%$ vs. Debate $>75\%$ on split evidence, confirming Proposition 3.1 and Route I).
3. **Experiment C — Route II (Verifier Gating $V \in R_{\mathrm{sys}}$) & Route III (Cross-Model Diversity $\rho_{\mathrm{het}} < \rho_{\mathrm{hom}}$):**
   - **Route II:** Gate round-to-round answer changes on `GSM8K` / `MATH` with a Python SymPy/unit-test check; verify $\hat{\tau}_{c\to i} \to 0.00$ via `pace dynamics`.
   - **Route III:** Compare Homogeneous 3-Agent Panel (`Llama-3.1-8B` $\times 3$) vs. Heterogeneous 3-Agent Panel (`Llama-3.1-8B` + `Qwen2.5-7B` + `DeepSeek-R1-Distill-14B` / `Gemma-2-9B`) under both Category B Majority Voting ($T=1$) and Multi-Agent Debate ($T=2$).

### Task 5: Package for One-Command TMLR Reproducibility Certification
Add a root `Makefile` and `reproduce_all.sh` that runs all unit tests (`pytest`), regenerates all 13 tables and 11 figures from the CSV/JSONL evidence files, and compiles both `main.pdf` and `tmlr_submission.pdf` in a single command.

---

## 4. Ecosystem & Community Adoption Multipliers (+80% Citation Boost)

1. **Publish `pace-eval` on PyPI (`pip install pace-eval`):** Global CLI installation without manual `PYTHONPATH` setup.
2. **One-Command OpenReview Rebuttal Generator (`pace report --format openreview`):** Copy-pasteable Markdown table with $\mathbf{R}$, Category A $\Delta$, Category B $\Delta$, Sampling Gap $\Delta_{\mathrm{gap}}$, and pre-formatted citation.
3. **Host the 531-Row Dataset on Hugging Face Datasets:** `load_dataset("mahmoudsajjadi/pace-multi-agent-bench")`.
4. **Interactive Hugging Face Space ("The PACE Baseline & Frontier Calculator"):** Upload 4 numbers $\rightarrow$ download Figure 2 accounting decomposition PDF, Figure 7 Empirical Study Ladder plot, and pre-filled LaTeX PACE Evaluation Card (Table 4).
5. **3-Line Auto-Instrumentation Hooks (`pace.autolog()`):** Hook into `litellm.completion` and `openai.ChatCompletion` for AutoGen, LangGraph, CrewAI, and LiteLLM.
6. **Pull Requests to Evaluation Harnesses:** Contribute the 500-item `pace hidden-profile` benchmark to `lm-evaluation-harness` and `inspect_ai`.
7. **Target Both TMLR Certifications:** Request **Survey Certification** and **Reproducibility Certification** (plus **Featured Certification** for J2C).
8. **Targeted Author Notification:** Send a brief, collegial email with the arXiv link to corresponding authors of the 9 synthesized studies and 2026 reproducibility papers cited in Section 2.

---

# Part II: Extended Brainstorm (Acceptance, Citations to 2035, Critique, Improvements, +80% Citation Levers)

> [!NOTE]
> All acceptance probabilities and citation counts below are subjective planning estimates, not measurements. Comparable papers vary widely; use these as targets, not predictions.

## 5. Current Acceptance Chance (Estimate, Current arXiv v1)

| Venue | Current | After Phase 17 | Main Reason |
| --- | --- | --- | --- |
| TMLR (accept) | 85%--92% | 94%--97% | TMLR judges correctness and evidence, not novelty; the synthesis and hedges fit well |
| TMLR Survey Certification | 40%--55% | 70%--80% | Needs a systematic (PRISMA) search |
| TMLR Reproducibility Certification | 35%--50% | 70%--80% | Needs real traces and one-command rebuild |
| TMLR Featured Certification (J2C) | 15%--25% | 35%--50% | Needs new primary evidence (live runs) |
| NeurIPS Datasets & Benchmarks | 45%--55% | 65%--75% | Ledger + hidden-profile benchmark fit the track |
| ICML / NeurIPS main | 25%--35% | 40%--55% | Reviewers expect new experiments |
| ICLR main | 25%--35% | 40%--50% | Same |
| ACL / EMNLP main or Findings | 35%--45% / 55%--65% | 50%--60% / 70%--80% | Findings is a realistic fallback |
| JAIR / ACM Computing Surveys | 60%--70% | 75%--85% | Strong survey/meta-analysis fit; slower review |

## 6. Citation Forecast Year by Year to 2035 (Estimate)

| Year | Conservative (annual / cum.) | Baseline (annual / cum.) | Boosted +80% (annual / cum.) |
| --- | --- | --- | --- |
| 2027 | 15 / 15 | 35 / 35 | 65 / 65 |
| 2028 | 40 / 55 | 90 / 125 | 165 / 230 |
| 2029 | 65 / 120 | 145 / 270 | 260 / 490 |
| 2030 | 75 / 195 | 165 / 435 | 300 / 790 |
| 2031 | 70 / 265 | 150 / 585 | 270 / 1,060 |
| 2032 | 60 / 325 | 125 / 710 | 225 / 1,285 |
| 2033 | 50 / 375 | 105 / 815 | 190 / 1,475 |
| 2034 | 45 / 420 | 90 / 905 | 160 / 1,635 |
| 2035 | 40 / 460 | 75 / 980 | 135 / 1,770 |

**Drivers of each scenario:**
- **Conservative:** TMLR acceptance only, no tooling adoption, topic interest in multi-agent debate fades after 2029.
- **Baseline:** TMLR acceptance + used as the standard citation for "compare against self-consistency at matched compute."
- **Boosted:** PyPI tool, HF dataset/Space, harness integration, J2C presentation, and a follow-up paper series that cites it.

## 7. Critique of the Paper (Reviewer Perspective)

### A. Scientific / Methodological
1. **No new primary experiments:** propositions are illustrated on simulated fixtures, not live transcripts.
2. **Purposive selection of the initial five studies;** no systematic search protocol (selection bias).
3. **Pareto dominance not verified per contrast;** 74% is an upper bound.
4. **Route III (heterogeneous debate) not extracted** (Zhang et al. Heter-MAD).
5. **Assumed item correlation** (φ = 0.50) rather than estimated from item-level data.
6. **Non-independence:** many contrasts per study; one study (e.g., Jwalapuram et al.) can dominate counts. Reviewers will want study-weighted results up front.
7. **κ ≈ 0.82 / p* ≈ 0.45 is a calibration,** not a measurement; risk of being read as a finding.
8. **Benchmark mix skewed to math/QA;** little on coding, agentic tool use, long-horizon planning, or open-ended generation.
9. **Model vintage:** many source studies use 2024–2025 models; reviewers may ask whether conclusions hold for newer reasoning models.
10. **Cost metrics heterogeneous across studies** (tokens vs. dollars vs. calls); cross-study comparability of R is partial.
11. **Single author + AI-assisted extraction:** no second human rater; inter-rater κ absent (hand-verification checklist still blank).
12. **Preregistration not registered** before analysis; the OSF protocol is a draft.

### B. Presentation
1. Main text ~20 pages before references (TMLR prefers concise; target 15–17).
2. Many acronyms/categories (A–D, Routes I–III, R dimensions); a one-page glossary/figure would help.
3. Contribution list long; lead with the single headline (baseline choice flips the sign).
4. Known typos (Section 3, Task 1).

## 8. Suggested Improvements (Mapped to Critiques)

| # | Critique | Fix | Effort |
| --- | --- | --- | --- |
| 1 | No live runs | Experiments A–C (Task 4) | 2–5 days GPU |
| 2 | Purposive selection | PRISMA API search + dual screening (Task 3) | 3–5 days |
| 3 | Pareto upper bound | Per-contrast resource check (Task 2) | 1 day |
| 4 | Heter-MAD | Extract Zhang et al. Table 4 (Task 2) | 2 hours |
| 5 | Assumed φ | Estimate φ̂ from Experiment A item vectors; φ sensitivity already exists | with Exp. A |
| 6 | Non-independence | Put study-weighted means and leave-one-study-out in main text | 0.5 day |
| 7 | κ calibration | Replace with measured κ̂ from live logs; keep calibration as illustration | with Exp. A |
| 8 | Benchmark mix | Add one coding (HumanEval+/MBPP+) and one agentic task to Experiment A | 1–2 days |
| 9 | Model vintage | Add one current reasoning model (open-weight) to live runs | with Exp. A |
| 10 | Cost heterogeneity | Table mapping each study's cost unit to R; flag non-comparable cells | 0.5 day |
| 11 | Single rater | Recruit one colleague to double-extract a 20%--40% stratified sample; report κ | 2–3 days (colleague) |
| 12 | Preregistration | Register the PRISMA update protocol on OSF before running the search | 1 hour |
| B1 | Length | Move proofs/extra tables to appendix; target 15–17 pages | 1 day |
| B2 | Acronyms | Add notation box / glossary figure | 2 hours |

## 9. Ways to Increase Citations by +80% (Complete List)

### A. Make it the default tool (highest leverage)
1. `pip install pace-eval` on PyPI with a 60-second README quickstart.
2. `pace.autolog()` hooks for OpenAI, LiteLLM, AutoGen, LangGraph, CrewAI, DSPy.
3. `pace report --format openreview` rebuttal table with built-in citation.
4. `pace card` producing a LaTeX/Markdown "PACE Evaluation Card" users paste into papers (with `\cite`).
5. BibTeX printed by every CLI command and in `CITATION.cff` (GitHub "Cite this repository" button).

### B. Make the data and benchmark easy to reuse
6. Hugging Face Dataset (531-contrast ledger) with dataset card and citation.
7. Hugging Face Space: PACE Baseline & Frontier Calculator.
8. Hidden-profile task registered in `lm-evaluation-harness`, `inspect_ai`, and OpenCompass.
9. Living leaderboard: PRs add new contrasts; release dated snapshots (each with a Zenodo DOI).
10. Papers with Code / "Papers with Code"-style task page for "compute-matched multi-agent evaluation."

### C. Venue and certification strategy
11. TMLR with Survey + Reproducibility (+ Featured) certification requests.
12. J2C presentation at ICLR/ICML/NeurIPS if Featured.
13. Workshop talks/posters (NeurIPS/ICLR workshops on agents, reasoning, evaluation) linking the TMLR paper.
14. A short companion paper (e.g., the live hidden-profile study) that cites and extends the synthesis.

### D. Discoverability and indexing
15. Google Scholar profile claimed; arXiv, Zenodo, OpenReview versions merged.
16. ORCID linked to arXiv, Zenodo, GitHub, OpenReview.
17. Semantic Scholar author page claimed; abstract/TL;DR checked.
18. Descriptive title keywords already present ("multi-agent," "test-time compute"); reuse identical keywords in GitHub topics, HF tags, Zenodo keywords.
19. arXiv v2 cross-listing (cs.CL, cs.AI, cs.MA) if not already done.

### E. Community outreach
20. Collegial emails to authors of the nine synthesized studies and cited 2026 reproducibility papers.
21. Thread on X/Bluesky/LinkedIn with the single headline figure (baseline category flips the sign).
22. Short blog post / explainer (personal site or Medium) with interactive figure.
23. Talk at UNR and invited lab talks (record and post on YouTube).
24. Reply helpfully (with the tool, not self-promotion) in GitHub issues/discussions of multi-agent frameworks asking about baselines.
25. Offer the PACE checklist to workshop organizers / reviewer guidelines for agent tracks.

### F. Long-term
26. Annual "State of Compute-Matched Multi-Agent Evaluation" update (v2026, v2027…), each with a DOI.
27. Extend to agentic/tool-use and coding settings (new paper, cites the original).
28. Teaching material: a notebook/tutorial used in courses on LLM evaluation.

## 10. Priority Order (What to Do First)

1. Task 1 typos + Task 2 (Heter-MAD, Pareto check) → arXiv v2 (1–2 days).
2. PyPI `pace-eval` + HF Dataset + CITATION/BibTeX in CLI (1–2 days).
3. Register PRISMA protocol on OSF, then run search (Task 3).
4. Live Experiments A–C (Task 4) + reproducibility packaging (Task 5).
5. Submit to TMLR with certification requests.
6. Outreach (author emails, social thread) right after arXiv v2.
7. HF Space, autolog hooks, harness PRs during TMLR review.
