# Phase 13: Field-Wide Baseline Audit, Re-Run Harness, Rollout Cards Integration, and Community Ecosystem Plan

> **Strategic Objective:** Move the paper from a strong synthesis to the canonical citation standard (1,250+ citations by 2035) by pairing our controlled experiments and theoretical propositions with:
> 1. **Field-Wide Baseline Prevalence Audit** (2023–2026) with dual human coding (Cohen's $\kappa$).
> 2. **Third-Party Reference Re-Runs** via `cme proxy` against matched self-consistency.
> 3. **Standards Compatibility** with *Rollout Cards* (`arXiv:2605.12131`) and *Holistic Agent Leaderboard*.
> 4. **Complete Literature Coverage** screening recent 2024–2026 papers (`arXiv:2606.20695`, `arXiv:2402.18272`, `arXiv:2602.09341`, *ReproEvalCard*).
> 5. **One-Command Consumer GPU Reproduction** & Google Scholar citation hygiene.

---

## 1. Patterns from Canonical Methodology Papers

| Canonical Paper | Mechanism for Citation Dominance | Our Equivalent |
| :--- | :--- | :--- |
| **Dodge et al. (2019)** (*Show Your Work*) | Equal-budget comparison curve + simple estimator + code | One-function estimator for the self-consistency frontier gap (`cme report`) |
| **Mitchell et al. (2019)** / **Gebru et al. (2021)** (*Model Cards* / *Datasheets*) | Named one-page template attached to papers | One-page CME Compute Block compatible with *Rollout Cards* |
| **Henderson et al. (2018)** (*Deep RL That Matters*) | Showed common practices flip conclusions + guidelines | Baseline ladder (A–D) audit + 6-item reviewer checklist |
| **Melis et al. (2018)** / **Dacrema et al. (2019)** / **Musgrave et al. (2020)** | Re-ran published methods under equal tuning budgets | Re-run published MAS methods with their released code via `cme proxy` vs. matched SC |
| **Kapoor & Narayanan (2023)** | Audited papers across fields + taxonomy + checklist | Multi-agent baseline taxonomy + field-wide prevalence audit |
| **Liu et al.** (*Lost in the Middle*) | One named phenomenon + one curve | Conformity threshold plot ($p^*$ crossover) |
| **Huang et al. (2024)** (*LLMs Cannot Self-Correct*) | Title names the confound + minimal control experiment | Plain title/abstract + Stasser & Titus hidden-profile positive control |

---

## 2. Sequenced Execution Roadmap (Single Author)

1. **Before Submission (Phase 10 / Immediate):**
   - Restore page-1 AI-use footnote (TMLR FAQ requirement).
   - Identical truthful verification wording across Open Science, Appendix E.7, §5.1, and Figure 4.
   - Downgrade Theorem 3.1/3.2 to **Propositions** citing Condorcet (1785), Ladha (1992), and Kish (1965); move $\kappa \approx 0.82$ to Appendix as fitted illustration; add scope note on $p_1$ vs. greedy decoding.
   - Remove `in progress` / `n/a` placeholders from default Table 4 build; add strict build gates in `assemble_paper.py`.
   - Complete the 2×2 positive control (`llama3.1:8b`, `qwen3:14b`, `gpt-oss-20b`) and main controlled comparison (`MMLU-Pro`, `MATH-500`).
2. **At Submission:**
   - Release paper, code (`cme`), and data (`hidden_profile`, `baseline_tier_rows`) simultaneously under TMLR preprint policy.
   - Freeze title prior to arXiv submission (avoid Google Scholar citation splitting); set paper as `preferred-citation` in `CITATION.cff`; keep identical metadata across versions.
   - Ship one-command 12 GB consumer GPU reproduction script with measured runtime.
   - Share 1-figure visual summary with practitioner digests (e.g., DAIR.AI) and publish Chinese-language summary/README.
3. **Companion / Wave 2 (2–4 Months Post-Submission):**
   - **Field-Wide Baseline Audit (150–300 papers, 2023–2026):** Automated arXiv + Semantic Scholar pull, LLM pre-fill, blind 20% dual human coding with Cohen's $\kappa$, longitudinal trend plot.
   - **Third-Party Reference Re-Runs:** Execute released multi-agent repositories through `cme proxy` against matched self-consistency on their native benchmarks (`"After matching compute, X of N reported gains remain"`).
   - **Ecosystem Expansion:** Teaching kit (notebook, slides, assignment), interactive theory slider explainer, and benchmark spin-off paper (natural-language hidden profiles across multiple domains).
4. **Ongoing:**
   - Quarterly leaderboard updates on new open-weight models.

---

## 3. New Literature & Standards to Integrate

1. **ReproEvalCard (ACL 2026 short):** Audited 55 LLM pipeline papers for reproducibility artifacts; cite to contrast artifact completeness with our baseline-strength audit. (`https://aclanthology.org/2026.acl-short.22.pdf`)
2. **Rollout Cards (`arXiv:2605.12131`):** Reproducibility standard for agent research. Map our 6D resource vector $\mathbf{R}$ onto a compatible Rollout Cards compute section instead of competing as an isolated standard.
3. **How Much Coordination Gain Is Real? (`arXiv:2606.20695`):** Paired noise-floor protocol for multi-agent benchmark differences; screen and cite in Related Work.
4. **Rethinking the Bounds of LLM Reasoning (`arXiv:2402.18272`, ACL 2024):** Early demonstration that well-prompted single agents match multi-agent discussion.
5. **AgentAuditor (`arXiv:2602.09341`):** Uses majority voting as its multi-agent baseline; cite as evidence of shifting field norms.
6. **External Resource:** 40-paper multi-agent reimplementation collection (noting shared history turning independent samples into paraphrases).
