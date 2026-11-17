# PACE Indexing & Visibility Execution Playbook

**Paper:** *More Agents, More Samples, or More Thinking? Untangling Coordination, Ensembling, and Test-Time Compute in Multi-Agent LLMs*  
**Identifiers:** `arXiv:2611.17610` · `Zenodo DOI: 10.5281/zenodo.24286397` · `github.com/mahmoudsajjadi/pace` · `huggingface.co/spaces/sajjadi/pace-studio`

---

## 1. Immediate GitHub & GitHub Pages Activation (5 Minutes)

1. **Push staged release (`dist/github_release_staging/`):**
   - Ensure `docs/index.html`, `docs/robots.txt`, `docs/sitemap.xml`, `docs/llms.txt`, and `.github/workflows/pages.yml` are on `main`.
2. **Enable GitHub Pages:**
   - GitHub Repo -> **Settings** -> **Pages** -> **Source**: select **GitHub Actions**.
   - Verify live URL: `https://mahmoudsajjadi.github.io/pace/` and `https://mahmoudsajjadi.github.io/pace/sitemap.xml`.
3. **Set GitHub Repository Metadata (About sidebar -> gear icon):**
   - **Description:** `PACE: Parity-Aware Compute Evaluation for Multi-Agent LLMs (arXiv:2611.17610) — 4-rung baseline ladder, 6D resource vector, 834-contrast ledger, CLI & Studio`
   - **Website:** `https://mahmoudsajjadi.github.io/pace/`
   - **Topics (add all):** `multi-agent-llm`, `test-time-compute`, `test-time-scaling`, `self-consistency`, `llm-evaluation`, `llm-debate`, `benchmarking`, `arxiv-2611-17610`, `parity-aware-compute-evaluation`
4. **Create a GitHub Release (`v0.2.2`):**
   - Tag `v0.2.2`, title `PACE v0.2.2 (arXiv:2611.17610)`, link Zenodo DOI `10.5281/zenodo.24286397` and arXiv `2611.17610`.
   - Enable Zenodo-GitHub webhook (`zenodo.org/account/settings/github/`) if you want future tags auto-archived.

---

## 2. Search Engine & Academic Indexer Submissions (15 Minutes)

1. **Google Search Console (`search.google.com/search-console`):**
   - Add property `https://mahmoudsajjadi.github.io/pace/` (URL prefix, verify via HTML tag or GitHub Pages).
   - Submit sitemap: `https://mahmoudsajjadi.github.io/pace/sitemap.xml`.
   - Run **URL Inspection** -> **Request Indexing** on `https://mahmoudsajjadi.github.io/pace/`.
2. **Bing Webmaster Tools (`bing.com/webmasters`):**
   - Import from Google Search Console (1-click) and submit `https://mahmoudsajjadi.github.io/pace/sitemap.xml`.
   - This feeds **Bing, DuckDuckGo, and AI answer engines**.
3. **Google Scholar (`scholar.google.com`):**
   - `docs/index.html` now includes Highwire Press `citation_*` tags (`citation_title`, `citation_author`, `citation_arxiv_id`, `citation_doi`, `citation_pdf_url`).
   - Open your Google Scholar Profile -> `+` -> **Add articles** -> search `2611.17610` (or add manually if arXiv has not propagated yet, then merge once auto-indexed).
4. **Semantic Scholar (`semanticscholar.org`):**
   - Search `2611.17610` or `More Agents, More Samples, or More Thinking?`.
   - Claim your author profile and link the official GitHub repo (`https://github.com/mahmoudsajjadi/pace`) and project page (`https://mahmoudsajjadi.github.io/pace/`).
5. **ORCID (`orcid.org`):**
   - Add `arXiv:2611.17610` (via arXiv/CrossRef/Zenodo DOI `10.5281/zenodo.24286397`) to **Works** on your ORCID record.
   - This propagates metadata to **OpenAlex**, **CrossRef**, **Europe PMC**, and **BASE (Bielefeld Academic Search Engine)**.
6. **DBLP / OpenAlex / Papers With Code / CatalyzeX / Zenodo / Google Dataset Search:**
   - **arXiv `Comments:` field (v2 metadata update):** Ensure the arXiv `Comments:` line includes `Code: https://github.com/mahmoudsajjadi/pace | Studio: https://huggingface.co/spaces/sajjadi/pace-studio`. Automated harvesters (Papers With Code, Semantic Scholar, Hugging Face, CatalyzeX) parse the arXiv `Comments:` field to attach official code badges.
   - **Zenodo Related Identifiers (`10.5281/zenodo.24286397`):** Edit the live Zenodo record to add `isSupplementTo: arXiv:2611.17610`, `isIdenticalTo: https://github.com/mahmoudsajjadi/pace`, and `isDescribedBy: https://mahmoudsajjadi.github.io/pace/`. This propagates to **DataCite**, **OpenAIRE**, **OpenAlex**, and **Google Dataset Search**.
   - **Google Rich Results & Dataset Search (`search.google.com/test/rich-results`):** Validate `https://mahmoudsajjadi.github.io/pace/` so the `Dataset`, `ScholarlyArticle`, `SoftwareSourceCode`, and `WebApplication` JSON-LD entities are indexed.
   - **IndexNow (`api.indexnow.org`):** After GitHub Pages is live, ping IndexNow for instant Bing, DuckDuckGo, and AI search engine crawling.
   - **Hugging Face Paper Page (`https://huggingface.co/papers/2611.17610`):** Link GitHub repo `mahmoudsajjadi/pace`, Space `sajjadi/pace-studio`, and datasets `sajjadi/pace-contrasts` + `sajjadi/hidden-profile-control`.
   - **alphaXiv (`https://www.alphaxiv.org/abs/2611.17610`):** Post the 4 Open Challenges from `docs/COMMUNITY_AND_PR_PLAYBOOK.md` as the top author comment, linking PACE Studio and `pip install pace-eval`.
   - **CatalyzeX / Papers With Code / Emergent Mind:** Submit `https://arxiv.org/abs/2611.17610` paired with `https://github.com/mahmoudsajjadi/pace`.

---

## 3. Hugging Face & PyPI Discoverability (10 Minutes)

1. **Sync Hugging Face Space (`dist/hf_space_pace_studio/` -> `huggingface.co/spaces/sajjadi/pace-studio`):**
   - Push updated `index.html` (with `citation_*`, Schema.org JSON-LD, and canonical tags) and `README.md` (with expanded tags and official links).
2. **Publish `pace-eval` to PyPI (from `dist/github_release_staging/`):**
   ```bash
   python -m build
   twine upload dist/*
   ```
   - Makes `pip install pace-eval` work globally from any terminal, Colab, or CI runner.
   - Also ensures **PyPI**, **Libraries.io**, and **PePy** index the package and link back to `arXiv:2611.17610` and `github.com/mahmoudsajjadi/pace`.

---

## 4. High-Leverage Community PRs & Announcements

See [`COMMUNITY_AND_PR_PLAYBOOK.md`](COMMUNITY_AND_PR_PLAYBOOK.md) for ready-to-paste PRs to:
- **UK AISI Inspect AI** (`UKGovernmentBEIS/inspect_ai` / `inspect_evals`)
- **UC Berkeley MAST** (`multi-agent-systems-failure-taxonomy/MAST`)
- **Princeton HAL** (`princeton-pli/hal-harness`)
- **Rollout Cards** (`arXiv:2605.12131`)
- **Curated Paper Lists** (`kyegomez/awesome-multi-agent-papers`, `vivy-yi/awesome-agent-orchestration`, `WooooDyy/LLM-Agent-Paper-List`)

### Ready-to-Post Community Summary (Hacker News / Reddit `r/MachineLearning` / `r/LocalLLaMA` / LinkedIn)

> **Title:** More Agents, More Samples, or More Thinking? Untangling Coordination, Ensembling, and Test-Time Compute in Multi-Agent LLMs (arXiv:2611.17610)
>
> Many multi-agent LLM papers compare a communicating multi-agent system against a single greedy pass ($k=1$), confounding inter-agent communication with independent sampling and expanded test-time compute.
>
> We introduce **Parity-Aware Compute Evaluation (PACE)**:
> - A **4-rung baseline ladder** (A: greedy, B: sampled voting, C: budget-matched, D: Pareto frontier)
> - A **6-dimensional resource vector** (thinking tokens, total tokens, cost, latency, sample count, external tool/verifier calls)
> - A **9-study synthesis** (`516` unique multi-agent configurations, `834` contrasts): across `474` Category B/C contrasts (`8` studies), multi-agent systems fail to lead in **`74%`** (mean $\Delta = -0.042$, REML $\hat{\beta} = -0.195$). Switching from greedy to sampled baselines lowers accuracy differences by `-0.038` across 5 dual-baseline studies (`318` pairs, `72` unique cells).
> - **Controlled `llama3.1:8b` experiments:** Shared-evidence MMLU-Pro (`n=250`) debate (`-0.015`) and MoA (`-0.072`) do not clear the equal-token self-consistency frontier, whereas a complementary Hidden Profile split-view control (`n=200`) shows `+0.073` frontier gain (`p = 0.007`).
>
> - Paper: https://arxiv.org/abs/2611.17610
> - Project Page: https://mahmoudsajjadi.github.io/pace/
> - Interactive Studio (no install): https://huggingface.co/spaces/sajjadi/pace-studio
> - Code & CLI (`pip install pace-eval`): https://github.com/mahmoudsajjadi/pace
