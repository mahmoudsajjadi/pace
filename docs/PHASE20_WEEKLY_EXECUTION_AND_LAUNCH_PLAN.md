# Phase 20: Weekly Execution Plan (Nov 12, 2026 -- Feb 21, 2027) & Launch Strategy

**Core Strategy:** TMLR first (primary archival journal), arXiv visibility immediately, PACE adoption next. Do not submit the same manuscript simultaneously to another journal or conference.

---

## 1. Immediate arXiv & TMLR Status Rules

1. **arXiv Submission (`arXiv:submit/8368121 [cs.AI]`):**
   - This is a submission-processing ID, not the final public arXiv ID.
   - Check the submission dashboard and email for moderation/announcement (accounting for the Nov 10--12 / Nov 15 Eastern announcement schedule). Do not withdraw if delayed.
   - Before any replacement, resolve: (a) the AI-use disclosure inconsistency between the arXiv PDF and the earlier TMLR draft, and (b) ensure no unassigned Zenodo DOI or submission ID is presented as final.
2. **TMLR Submission Strategy:**
   - Stay with **TMLR** (compatible with arXiv preprints; no parallel archival submissions).
   - **Length optimization:** Aim to compress the main narrative from ~26 pages to ~12--16 pages before references/appendices (TMLR warns >12 pages can lengthen review), moving detailed extraction tables, secondary sensitivity analyses, full proofs, and listings to appendices without dropping inconvenient results.
   - Do not unilaterally replace an in-review TMLR manuscript; respond to actual reviews with targeted revisions.
   - **ICLR 2027 J2C (Dec 18, 2026, capacity 150):** Treat as a conditional bonus only if TMLR publication + qualifying certification (J2C/Featured/Outstanding) are completed in time; otherwise target the next eligible J2C cycle.

---

## 2. Week-by-Week Execution Calendar (Nov 12, 2026 -- Feb 21, 2027)

### November: Launch & Scientific Corrections
- **Week 1 (Nov 12--15) — arXiv posting:** Monitor moderation/announcement; save final public arXiv ID and URL; verify PDF, title, author, abstract, references, and source package.
- **Week 2 (Nov 16--22) — Public launch:** Publish concise research summary, PACE README quickstart, BibTeX, baseline-ladder graphic, and data links on GitHub (frame PACE as a proposed protocol and tool, not an established standard).
- **Week 3 (Nov 23--29) — Evidence audit:** Rebuild 9-study extraction; verify 516 configurations and 531 raw rows; extract `Heter-MAD` (Zhang et al. Table 4); resolve AGIEval `N=100` placeholder.
- **Week 4 (Nov 30--Dec 6) — Statistical corrections:** Recompute Category A/B/C results, study-level averages, sampling gaps, sensitivity estimates, and abstract numbers; document pooled model limitations.

### December: Scientific Strengthening
- **Week 5 (Dec 7--13) — Manuscript V2 design:** Correct AI-use disclosure, verify bibliography/metadata, refine resource vector definitions, revise abstract/limitations.
- **Week 6 (Dec 14--20) — Certification decision:** Check TMLR status; evaluate Dec 18 ICLR 2027 J2C eligibility (apply only if published with qualifying certification).
- **Week 7 (Dec 21--27) — Real PACE validation:** Run a genuine local-model trace through PACE; verify tokens, model calls, tool calls, timestamps, retries, cost calculations, and latency.
- **Week 8 (Dec 28--Jan 3) — Reproducibility package:** Organize verified data, scripts, configs, test output, installation instructions, and archive-ready files.

### January: Evidence That Makes PACE Adoptable
- **Week 9 (Jan 4--10) — Heterogeneity experiment:** Compare homogeneous vs. heterogeneous independent sampling against communication-based systems using feasible local models; publish configs and real traces.
- **Week 10 (Jan 11--17) — Evidence partition experiment:** Compare shared-context agents vs. complementary partitioned-evidence agents vs. single-agent full-evidence baseline.
- **Week 11 (Jan 18--24) — PACE software release candidate:** Schema validation, clean install, test coverage, reporting, genuine trace example, and installation guide.
- **Week 12 (Jan 25--31) — External reproducibility:** Have an independent researcher/tester follow the package instructions; fix issues and document what was reproduced.

### February: Consolidate & Position for Recognition
- **Week 13 (Feb 1--7) — Manuscript V2:** Incorporate verified corrections, `Heter-MAD`, improved analysis, and live PACE validation (keep uncompleted experiments out of empirical claims).
- **Week 14 (Feb 8--14) — Dissemination:** Publish technical tutorial, short demo, and source-linked evidence registry.
- **Week 15 (Feb 15--21) — Publication decision strategy:** Address actual TMLR reviews if available; prepare a distinct future conference study only if new evidence justifies it.

---

## 3. Three Prioritized Experiments

1. **Experiment 1 (Highest Priority): Heterogeneous vs. Homogeneous Agents** — Does model diversity help beyond independent sampling and beyond the strongest individual model? (Addresses omitted `Heter-MAD` case.)
2. **Experiment 2: PACE with Real Traces** — Verify token counts, call counts, latency, concurrency, tool usage, and missing-value handling on genuine model requests/responses.
3. **Experiment 3: Shared vs. Partitioned Evidence** — Compare identical prompts, overlapping evidence, distinct partitions, and single-agent union baseline.

*(Start with local, affordable models and small pilots; do not spend on paid APIs before demonstrating that the setup distinguishes communication from additional sampling.)*

---

## 4. Calibrated Citation Forecast (2026--2035) & +50% Target

| Year | Low | Base Case | +50% Target | Strong Adoption |
| --- | --- | --- | --- | --- |
| 2026 | 0 | 0 | 0 | 1 |
| 2027 | 1 | 4 | 6 | 8 |
| 2028 | 3 | 8 | 12 | 18 |
| 2029 | 5 | 12 | 18 | 28 |
| 2030 | 7 | 16 | 24 | 38 |
| 2031 | 8 | 19 | 29 | 45 |
| 2032 | 9 | 21 | 32 | 50 |
| 2033 | 9 | 22 | 33 | 52 |
| 2034 | 8 | 21 | 31 | 50 |
| 2035 | 7 | 19 | 28 | 45 |
| **Total** | **57** | **142** | **213** | **335** |

### Five Highest-Value Interventions
1. **PACE software:** Reliable install, one-command audit, usable Python API, real trace support.
2. **Evidence registry:** Source-linked, versioned, downloadable study/configuration dataset.
3. **Interoperability:** Integrations with existing agent tracing and evaluation tools (e.g., OpenTelemetry, Inspect AI, LangGraph).
4. **Independent validation:** Reproducible experiments and external replication package.
5. **Tutorials and discovery:** Practical tutorials, talks, technical explainer, citation-ready materials.

*(Avoid spending months on a large custom GUI, repetitive social posts without new evidence, low-value benchmarks, duplicating existing trace standards, or a second survey paper.)*

---

## 5. Three-Moment Dissemination Plan

- **Moment 1 — arXiv Launch (within 48h of public posting):** Concise summary, one strong figure, manuscript + repo links, complete BibTeX, balanced framing (not *"multi-agent systems do not work"*).
- **Moment 2 — PACE Release (after tests & clean install pass):** Short demo, real trace audit, example output, schema + extraction dataset, DOI archive when authorized.
- **Moment 3 — Scientific Validation (after new experiments & external check):** `Heter-MAD` analysis, homogeneous/heterogeneous comparison, revised results/data, technical changelog; targeted outreach to 10--15 researchers for technical/integration feedback.
