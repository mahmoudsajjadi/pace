# Phase 21: Urgent Pre-Announcement arXiv Fixes & Integrity Checklist

> **Deadline:** Before arXiv announcement (**Friday, Nov 13, 11:00 a.m. Pacific / 2:00 p.m. Eastern**). Unsubmit, fix, and resubmit while still in `arXiv:submit/...` status so the first public version is clean.

---

## 1. Urgent Fixes Before arXiv Announcement

1. **Honest "Use of AI Tools" & Open Science Wording (P0):**
   - *Problem:* Current arXiv PDF says AI was used *"solely for language editing and grammar checking"*, contradicting earlier drafts, repo history, and TMLR's first-page footnote.
   - *Fix:* Replace with accurate disclosure (AI assistants were used to extract candidate values from source PDFs, screen candidate studies against written criteria, write analysis code / `pace` package / tests, run programmatic and stratified checks, check bibliographic metadata, and draft/edit text; state clearly what the author directed and verified vs. did not re-read by hand). Restore matching wording in Open Science.
2. **Abstract Overclaim:**
   - *Fix:* Narrow *"require partitioned evidence, external verification, or error diversity"* to state that communication cannot add information when agents share identical evidence, and that the paper derives three routes by which it can help.
3. **Reference Checks:**
   - **Reference [40] (AgentAuditor, `arXiv:2602.09341`):** Add missing author **Gengshuo Liu** (*Wei Yang, Shixuan Li, Gengshuo Liu, Heng Ping, Peiyu Zhang, Paul Bogdan, and Jesse Thomason*).
   - **Reference [41] (ReproEvalCard):** Verified correct.
   - **Reference [43]:** Unverified ("-3 to +18 points across two seeds") — open the arXiv page and verify authors/claim before keeping.
4. **Figure & Appendix Labels:**
   - **Appendix D:** Label synthetic test files as **synthetic test fixtures** (not "benchmark calibration traces").
   - **Figure 3B:** Label the $\kappa = 0.82$ Kim et al. ceiling as **illustrative** (chosen to reproduce 45%, not estimated).
   - **Figure 5:** Fix displaced hat on $\hat{\beta}$.
5. **arXiv CS Review-Article Rule & Cross-Listing:**
   - Put the formal results and `pace` tool first in the abstract and arXiv comments field (since arXiv CS requires documented prior peer review for literature surveys/position papers).
   - Cross-list to `cs.CL`, `cs.MA`, and `cs.LG`; pair **PACE** with its full name (*Parity-Aware Compute Evaluation*) everywhere.
6. **Secrets & Source-PDF Scan:**
   - Scan full git history for any pasted API keys (Groq/Google), revoke any exposed keys, and verify no copyrighted source-paper PDFs are in the public repo.

---

## 2. Announcement-Week & Next 6–10 Weeks

- **Announcement Week:** Submit to **Hugging Face Daily Papers** (within 7 days of arXiv version date); ensure README quickstart, `pip install`, Colab notebook, `CITATION.cff`, and Zenodo release are ready; share Figure 2 + Figure 3 thread; email cited authors (Tran & Kiela, Choi, Wunderlich, Jwalapuram, Kim, Masters, Pattnayak) to verify their numbers.
- **Next 6–10 Weeks (for `arXiv v2` & TMLR):** Complete hand verification & proof check, run $2 \times 2$ positive control on 3 models, run main comparison on MMLU-Pro + hard math, complete documented search with two screeners, and submit anonymized TMLR version (~12–15 main pages) with first-page AI-use footnote.
