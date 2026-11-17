# Venue length and format audit (checked 2026-11-09)

Current manuscript: 19 pages before the references (generic `article` class, 11 pt), about 8,900 words from abstract to references including captions and table text, abstract 339 words, 6 figures plus tables in the main text, 3 appendices (A: 3 pages, B, C; 7 pages in total).

Guideline wording below is taken from search results on each venue's own pages. Re-read the live pages before submitting. Pages move.

| Venue | Stated limits | Gap to the current paper |
|---|---|---|
| Nature Machine Intelligence, Article ([content types](https://www.nature.com/natmachintell/content)) | Main text 3,500 words (excludes abstract, Methods, references, figure legends); abstract up to 150 words, unreferenced; up to 6 display items; about 50 references; Introduction without heading, then Results, Discussion, Methods. | Large. The main text is about 2.5 times the limit, the abstract is more than twice the limit, and the section structure differs. |
| TMLR ([author guide](https://jmlr.org/tmlr/author-guide.html), [FAQ](https://jmlr.org/tmlr/faq.html)) | No hard page limit; length must be justified. Reviews are requested in 2 weeks up to 12 pages of main content before references, 4 weeks above. TMLR style file is mandatory. Appendix after the references is allowed, reviewers may skip it. | Small. The paper is 19 pages against the 12-page soft threshold, so expect the slower review track unless trimmed. Switching to the TMLR template is required. |
| NeurIPS 2026 Evaluations and Datasets track (formerly Datasets and Benchmarks) ([reviewing guidelines](https://neurips.cc/Conferences/2026/EvaluationsDatasetsReviewerGuidelines), [main-track handbook](https://neurips.cc/Conferences/2026/MainTrackHandbook)) | Main content 9 pages, official style, no formatting changes. Appendix allowed; code and data in a separate file. Authors must follow the NeurIPS policy on use of agents and LLMs. | Large. Nearly half the main text would need to move to the appendix. The track expects a dataset or benchmark contribution. |

I did not find the 2026 call text itself for the track. The 9-page figure comes from the 2026 reviewing guidelines.

## Recommendation

1. **TMLR is the closest fit.** Keep the structure, convert to the TMLR template, and trim the main text toward 12 pages by moving Appendix material (already done) and some of the per-benchmark discussion out of the body. No core finding needs to be deleted.
2. **NeurIPS Evaluations and Datasets** needs a 9-page version. Keep the abstract, the resource-vector definition, Figures 1 and 2, the multi-tier synthesis, the checklist, and the Pareto figure. Move Sections 2 and 3 detail, the threshold analysis, and Figures 5 and 6 to the appendix. The released ledgers, `mae-eval`, and the dashboard are the benchmark-style contribution and should be stated early.
3. **Nature Machine Intelligence** is a different paper. A 3,500-word Article with a 150-word abstract and Methods section would need the resource vector, the regime result, and one figure in the body, with the checklist and tables in Supplementary Information. Treat it as a rewrite and decide only after the TMLR or NeurIPS version exists.

## Disclosure of AI assistance

Every venue above has a policy on AI tools. NeurIPS holds authors responsible for all content and requires compliance with its LLM policy. The current manuscript has no AI-assistance statement. See the note in the session report: the statement should be restored in the form the author approves before any submission.
