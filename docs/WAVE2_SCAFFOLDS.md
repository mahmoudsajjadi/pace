# Wave 2 scaffolding (code only; no results)

Nothing in this file has been run on real papers or third-party repositories for the manuscript. The commands below are tested on synthetic inputs and a fake local server only.

## Field audit: `scripts/audit_pipeline.py`

`search` (fixed arXiv queries, 2023-01-01 to 2026-10-31, optional Semantic Scholar), `sheet` (blank coding sheet: baseline category A to D or none or unclear; six resource-dimension fields; item count; code release), `split` (rater A codes everything; a seeded random 20% also goes to rater B, who receives no codes from A), `kappa` (Cohen's kappa per field on the double-coded papers; refuses with exit status 1 while any double-coded cell is blank or invalid), `status` (counts of papers and blank cells only). There is no command that reports a prevalence figure; none will be reported until both human raters have finished. The LLM pre-fill columns are left empty by the scripts.

## Re-run harness: `scripts/rerun_harness.py`

Routes a locally cloned third-party codebase through `cme proxy` (new options `--item-file` and `--system-label`, so code that sends no headers is attributed to the item being run), runs it once per item, scores its output by regular expression, runs `cme baseline` (greedy plus a 16-sample pool, resumable) and `cme report` on the same items, and writes `rerun_manifest.json` with the repository's exact commit hash (the run is refused for a dirty tree or a commit different from `expected_commit`). It never clones, and it runs third-party code only with `--yes-run-third-party-code`; use a container or virtual machine. Limits: calls that bypass the proxy are not logged, streaming calls are rejected, items run serially, and regex exact-match scoring suits short-answer benchmarks only.

## Literature screen: `scripts/screen_literature.py`

Fixed author queries (Ferreira, Nguyen, Bertalanic, Ann, Zhu, ColMAD, Wynn), topic-filtered; writes `candidates.csv` and `candidates.md` with `decision` set to `pending`. It never edits the corpus.

## Rollout-card compute block: `cme report --export-rollout-card PREFIX`

Writes PREFIX.json, PREFIX.yaml and PREFIX.tex: rows for the annotations stream (namespace `cme.compute`) and a reporting-rule entry with a drops manifest, following Appendix E of arXiv:2605.12131. It is a compute block, not a complete rollout card, and has not been checked with the reference validator.
