# Phase 4 Author Directive & Execution Order for Claude Code

**To:** Claude Code  
**From:** Author (Seyed Mahmoud Sajjadi Mohammadabadi, University of Nevada, Reno)  
**Date:** November 10, 2026  
**Target:** Final TMLR Submission Package & Groundwork for 10,000+ Citations  

---

### Author Decisions on the 2 Blocking Questions

1. **Decision A (Dataset Scope): YES to $K=9$ (531 contrasts) as headline.**
   - Promote the full $K=9$ synthesis (531 contrasts) as the primary headline results across main tables, abstract, and text.
   - Retain $K=5$ (252 contrasts) reported side-by-side in Table 2 as the anchor sensitivity subset.
   - Fetch Yang (`2505.22960`), Zhang (`2502.08788`), and Smit (`2311.17371`) to record exact $N$ with page/section citations. Where an exact $N$ is omitted in the source paper, mark it as estimated and include the $N=100$ sensitivity check.

2. **Decision B (Dual-Baseline Framing): YES to restoring $-0.041$ with exact caption-quoting wording.**
   - Remove `UNRESOLVED BASELINE` tags from all captions and prose.
   - Restore $-0.041$ against five-sample CoT-SC in the abstract, figures, and tables.
   - Use the objective, caption-quoting language you proposed:
     > *"The source caption states that the single-agent CoT and CoT-SC rows 'report the best observed score across MAS system entries'; because per-entry baseline scores are not published, differences are computed against these reported rows, representing an upper-bound single-agent baseline."*
   - Harmonize Section 7.1 with Sections 1, 5, and 8 so the entire manuscript reports both baselines consistently ($-0.007$ vs. greedy CoT; $-0.041$ vs. 5-sample CoT-SC).

---

### Clarification on Human Verification Audit

- **Scientific Honesty:** Do **not** declare author second-pass complete.
- Generate `review/HUMAN_VERIFICATION_AUDIT.md` (35–40 stratified rows covering all 9 studies with source table, page number, verbatim extracted text, SAS baseline, MAS score, and calculated delta).
- Set the verification column to:
  `Automated text concordance: Verified | Author second-pass: Pending author review`
- In `manuscript/module5_open_science.tex`, update the disclosure to state:
  > *"Data extraction used automated concordance checks against rendered tables and text via `pdftotext`, paired with a stratified 40-row extraction audit ledger with verbatim source citations prepared for author review."*

---

### Protocol Split (Decision 1)

- Split into:
  - `protocol/META_ANALYSIS_PROTOCOL.md`: Locks retrospective meta-analysis registration, search queries, eligibility criteria, and synthesis models.
  - `protocol/PROSPECTIVE_PILOT_PROTOCOL.md`: prospective GPU cluster experiments, Slurm job templates, margin calculations ($\delta=0.02$, seed 42 as author decisions), and API pilot protocols.
  - `protocol/PROTOCOL.md`: clean index linking to both.

---

### What Antigravity Already Fixed for You (No Action Needed)

1. **Fabricated References Removed:** Deleted placeholder entries [28] and [30] (`illusion2025` with `arXiv:2502.00000`, `dapo2025` with `arXiv:2501.00000`) from `references.bib`.
2. **Artificial Table Cut:** Removed `table_influential_frameworks.tex` to eliminate citation engineering.
3. **Foundational Citations Added:** Section 2 now genuinely cites **Li et al. (TMLR 2024)** (*"More Agents Is All You Need"*, `li2024more`), connecting our title directly to TMLR's core literature, and **Kapoor et al. (ICLR 2026)** (*"Holistic Agent Leaderboard"*, `kapoor2026holistic`).
4. **Clean Build:** Both `main.pdf` (27 pages) and `tmlr_submission.pdf` (24 pages) compile with 0 errors, 0 undefined citations, and 0 overfull hboxes. 198 unit tests pass (100%).
5. **Stale file deleted:** `archive/tables/table2_piecewise.tex` archived.

---

### Step-by-Step Execution Checklist for Claude Code

1. **Verify Sample Sizes:** Fetch Yang, Zhang, and Smit from arXiv; verify or note $N$ with page citations.
2. **Promote $K=9$ (531 Contrasts):** Update `manuscript/module2_empirical_overhaul.tex`, `manuscript/tables/table2_sensitivity_matrix.tex`, and Figure 2 data to reflect $K=9$ pooled synthesis with $K=5$ sensitivity row.
3. **Dual-Baseline Narrative:** Restore $-0.041$, remove all `UNRESOLVED BASELINE` tags, and harmonize Section 7.1 with Sections 1, 5, and 8 using the caption-quoting disclosure.
4. **Split Protocol:** Create `protocol/META_ANALYSIS_PROTOCOL.md` and `protocol/PROSPECTIVE_PILOT_PROTOCOL.md` (margin $\delta=0.02$, seed 42).
5. **Generate Audit Sheet:** Create `review/HUMAN_VERIFICATION_AUDIT.md` (40 rows, pending author review) and update `module5_open_science.tex`.
6. **Draft Inquiry Email:** Write `review/email_to_jwalapuram_authors.txt` (kept local).
7. **Extract Tran 3 Arms:** Record the remaining three Tran arms (Roles, Ensemble, Centralized) as an appendix sensitivity check.
8. **Final Compilation & Test:** Run `python analysis/assemble_paper.py` and `pytest tests/ -v`.
