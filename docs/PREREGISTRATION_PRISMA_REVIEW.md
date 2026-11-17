# Systematic review protocol (PRISMA 2020): baseline strength in multi-agent LLM evaluations

**Status: READY FOR REGISTRATION (DRAFT. NOT REGISTERED).** The text below is complete for an OSF registration. Nothing in it has been executed: no search, screening or extraction has been run for this review. Registration is an external step and waits for the author's explicit approval and the OSF registration identifier, which is to be written into the field below. No live screening and no screening prevalence statistic is produced before registration.

## 1. Questions
- **RQ1.** Across published comparisons of multi-agent LLM systems with single-agent baselines, how large is the pooled accuracy difference when the baseline is sampled (Category B) or compute-matched (Category C)?
- **RQ2.** Is that pooled difference equivalent to zero within a margin of plus or minus 2 accuracy points (TOST), or is it outside the margin?
- **RQ3.** Do the differences vary with (Route I) split evidence across agents, (Route II) an external verifier available to the system, (Route III) heterogeneous models, or the baseline rung?
- **RQ4 (descriptive).** In what share of studies is a sampled or compute-matched baseline reported at all? This share is reported only after both raters have finished and the author approves.

## 2. Eligibility
Include a report if (1) it evaluates a multi-agent system of language models (two or more model instances exchanging messages or intermediate results, or an orchestrated workflow of model calls); (2) it reports accuracy or a success rate for that system and for at least one single-agent baseline on the same items; (3) scoring is objective (exact match, executable tests, verifier or fixed rubric, not model-judged preference alone); (4) results are in tables or text from which per-benchmark values can be read. Exclude reports without a single-agent baseline on identical items, reports of training methods whose comparison is a fine-tuned model, surveys and position papers, and duplicates (the most complete version is kept). Date window: 2023-01-01 to 2026-10-31 (searches repeated at registration and the end date recorded). Language: English.

## 3. Sources and fixed queries
arXiv and Semantic Scholar by API (queries in `scripts/prisma_search.py`: four arXiv queries, four Semantic Scholar queries, and the seven author queries of `scripts/screen_literature.py` so that Ferreira, Nguyen, Bertalanic, Ann, Zhu, Chen (ColMAD) and Wynn are screened); ACL Anthology and OpenReview by manual export imported with `prisma_search.py import`; backward and forward citation chasing from the nine seed studies through the Semantic Scholar graph API. Queries are not changed after registration except by a dated amendment.

## 4. Screening and extraction
Two independent human raters screen every record by title and abstract (include, exclude, maybe) and then every full text, in different random orders, with no decision pre-filled by any tool. Disagreements are resolved by discussion and then a third reader. Cohen's kappa is reported for title-and-abstract screening and for each categorical extraction field. One rater extracts every included study; the second extracts a seeded random 20% (`prisma_search.py sheets`). Extraction fields: baseline category (A, B, C, D), the six resource dimensions reported (yes, no, unclear), item and seed counts, code release, the three route moderators, risk-of-bias items, and the headline multi-agent and baseline accuracies with their table or page reference. LLM pre-fill is allowed only in a separate column that raters see after their own coding, never as a replacement.

## 5. Risk of bias (adapted rubric; each item low, some concerns, high, or unclear)
(a) Baseline strength and compute matching (is the baseline sampled or compute-matched, and is the matching resource named); (b) item, seed and contamination reporting (item counts, seeds or repeats, any contamination check); (c) selective reporting (maximum over settings, best configuration only, omitted benchmarks); (d) scoring validity. Risk of bias is reported per study and used in sensitivity analyses; it is not used to drop studies.

## 6. Moderators (pre-specified)
Route I split evidence (agents receive different parts of the evidence: 1, else 0); Route II verifier (an external verifier or executable check available to the system during inference: 1, else 0); Route III heterogeneous models (different model families among the agents: 1, else 0); baseline rung (C versus B). Each is coded from the paper only; "unclear" is allowed and the study is then excluded from that moderator's model.

## 7. Analysis
- Effect size: log odds ratio of multi-agent versus baseline accuracy with the Haldane-Anscombe correction and an assumed item correlation (primary 0.5, sensitivity 0 to 0.9), as in Table 3 of the manuscript.
- Model: three-level random effects (contrasts within studies) with CR2 cluster-robust intervals and Satterthwaite degrees of freedom; block covariance for contrasts that share a baseline as a sensitivity analysis. Implementation: `analysis/meta_regression.py`, `analysis/run_moderator_tost.py`.
- Equivalence: two one-sided tests on the pooled log odds ratio against a margin equal to 2 accuracy points converted to log odds at the mean baseline accuracy of the analysed set (about 0.08 at accuracy 0.535). Equivalence is concluded only if both one-sided p-values are below 0.05 (equivalently the 90% interval lies inside the margin); a non-significant test of difference is not read as equivalence.
- Moderator meta-regression: one moderator at a time, then Route I to III jointly if each has at least two studies at each level; a moderator with fewer is reported as not estimable.
- Comparison of the seed set (nine studies) with the expanded set; leave-one-study-out and a Category A versus B/C comparison as sensitivity analyses.
- Estimator checks: the simulations of `scripts/run_estimator_simulations.py` (`docs/SIMULATION_RESULTS.md`).

## 8. Reporting
PRISMA 2020 flow diagram (`prisma_search.py flow`) and checklist; a table of excluded full texts with reasons; a data file of all extracted rows; deviations from this protocol listed with dates.

## 9. Not covered
This protocol covers the literature review only. The confirmatory experiments have their own plan (`docs/PREREGISTRATION.md` and Addendum 1) and are not registered either.

## 10. Fixed search queries (verbatim from `scripts/prisma_search.py` and `scripts/screen_literature.py`)

Date window for all searches and all eligible reports: **2023-01-01 to 2026-10-31** (publication or first-posting date).

**arXiv API (`search_query`, sorted by submission date, up to 400 results per query):**

1. `all:"multi-agent" AND all:debate AND (all:LLM OR all:"language model")`
2. `all:"multi-agent" AND (all:LLM OR all:"language model") AND (all:reasoning OR all:benchmark)`
3. `all:"mixture-of-agents" OR all:"multi-agent debate" OR all:"multiagent debate"`
4. `all:"multi-agent collaboration" AND (all:LLM OR all:"language model") AND all:accuracy`

**Semantic Scholar graph API (`/paper/search`, 100 results per query, `publicationDateOrYear=2023-01-01:2026-10-31`):**

1. `multi-agent LLM debate`
2. `multi-agent LLM collaboration reasoning`
3. `mixture of agents language model`
4. `multi-agent debate single-agent baseline self-consistency`

**Author queries (arXiv, same window; the topic filter limits each surname query to multi-agent language-model papers):** topic filter `(all:"multi-agent" OR all:"multiagent" OR all:debate OR all:"agent collaboration") AND (all:LLM OR all:"language model")`

- Ferreira: `au:Ferreira AND (all:"multi-agent" OR all:"multiagent" OR all:debate OR all:"agent collaboration") AND (all:LLM OR all:"language model")`
- Nguyen: `au:Nguyen AND (all:"multi-agent" OR all:"multiagent" OR all:debate OR all:"agent collaboration") AND (all:LLM OR all:"language model")`
- Bertalanic: `au:Bertalanic AND (all:"multi-agent" OR all:"multiagent" OR all:debate OR all:"agent collaboration") AND (all:LLM OR all:"language model")`
- Ann: `au:Ann AND (all:"multi-agent" OR all:"multiagent" OR all:debate OR all:"agent collaboration") AND (all:LLM OR all:"language model")`
- Zhu: `au:Zhu AND (all:"multi-agent" OR all:"multiagent" OR all:debate OR all:"agent collaboration") AND (all:LLM OR all:"language model")`
- ColMAD: `all:ColMAD`
- Wynn: `au:Wynn AND (all:"multi-agent" OR all:"multiagent" OR all:debate OR all:"agent collaboration") AND (all:LLM OR all:"language model")`

**Citation chasing:** backward (references) and forward (citations) of the nine seed studies (Tran and Kiela 2026, Choi et al. 2025, Kim et al. 2026, Jwalapuram et al. 2026, Wunderlich et al. 2026, Ke et al. 2026, Yang et al. 2025, Zhang et al. 2025, Smit et al. 2024), resolved by exact title match on Semantic Scholar, restricted to the window.

**Manual exports:** ACL Anthology (title and abstract search for the terms "multi-agent", "debate", "mixture of agents" with "language model", window as above) and OpenReview (the same terms, venues of the window); imported with `prisma_search.py import`. The exact export dates and result counts are recorded at registration.

## 11. OSF registration form text

- **OSF registration identifier:** [to be supplied by the author after registration]
- **Title:** Baseline strength and compute matching in comparisons of multi-agent language-model systems with single-agent baselines: a systematic review and meta-analysis.
- **Description:** Systematic review following PRISMA 2020 of reports published from 2023-01-01 to 2026-10-31 that compare a multi-agent language-model system with a single-agent baseline on identical items. We extract accuracy for both, classify the baseline (greedy, sampled, compute-matched, budget sweep), and code three pre-specified moderators.
- **Hypotheses.** H-R1: the pooled log odds ratio of multi-agent versus sampled or compute-matched baseline is not zero. H-R2 (equivalence): the pooled effect lies within plus or minus 2 accuracy points (TOST). H-R3: effects are larger where evidence is split across agents (Route I), where an external verifier is available (Route II), or where the models are heterogeneous (Route III). The direction of H-R1 is not pre-specified.
- **Design:** systematic review, dual independent screening and extraction, random-effects meta-analysis with cluster-robust intervals.
- **Sampling plan:** all reports retrieved by Section 10 that meet Section 2; no sample-size target; the seed set of nine studies is analysed first and again together with the expanded set.
- **Variables:** Section 4 (extraction fields), Section 5 (risk of bias), Section 6 (moderators).
- **Analysis plan:** Section 7, including the TOST margin of plus or minus 2 accuracy points converted to log odds at the mean baseline accuracy.
- **Existing data / prior knowledge:** the nine seed studies were extracted before this registration (see `docs/PREREGISTRATION.md` for the earlier synthesis, which was not registered); the expanded set has not been searched, screened or extracted.
- **Deviations:** to be listed with dates in the final report.
- **Rater names and the registration date:** to be filled in at registration.

