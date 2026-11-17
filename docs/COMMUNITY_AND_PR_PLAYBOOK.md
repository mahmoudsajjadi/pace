# PACE Community, Ecosystem PR & Visibility Playbook

*(arXiv:2611.17610 · Zenodo `10.5281/zenodo.24286397` · `github.com/mahmoudsajjadi/pace`)*

## 1. Open-Source Ecosystem PR Targets (This Week)

1. **UK AISI Inspect AI (`UKGovernmentBEIS/inspect_ai` / `inspect_evals`)**
   - `code/pace/importers.py` and `code/pace/cli.py` now natively support `pace import-logs --format inspect`.
   - **PR Title:** `docs(evals): add PACE compute-parity & baseline-ladder audit recipe for multi-agent solvers`
   - **PR Body:**
     > When evaluating multi-agent solvers (e.g., debate, sub-agent delegation, or Mixture-of-Agents) in Inspect AI, comparing against a single pass ($k=1$) confounds inter-agent coordination with independent sample multiplicity and expanded test-time compute.
     >
     > This PR adds a lightweight recipe showing how to pipe Inspect AI JSON evaluation logs (`inspect log dump run.eval > inspect_run.json`) into **PACE** ([arXiv:2611.17610](https://arxiv.org/abs/2611.17610)) to classify the baseline on the 4-rung PACE Ladder, audit the 6-dimensional resource vector $\mathbf{R}$, and compute $k_{\mathrm{tok}}$ and round-to-round peer-influence flip rates ($\tau_{i\to c}$ vs. $\tau_{c\to i}$).
     > ```bash
     > inspect log dump logs/debate_run.eval > inspect_run.json
     > pace import-logs --format inspect --input inspect_run.json --output pace_trace.jsonl
     > pace card pace_trace.jsonl
     > pace dynamics pace_trace.jsonl --n-boot 200
     > ```
     > Browser option: https://huggingface.co/spaces/sajjadi/pace-studio
2. **UC Berkeley MAST (`multi-agent-systems-failure-taxonomy/MAST`)**: Add an example script auditing MAST traces with `pace dynamics` and `pace card`.
3. **Rollout Cards Standard (`arXiv:2605.12131`)**: Submit `pace report --export-rollout-card` (`pace.compute` namespace).
4. **Princeton HAL (`princeton-pli/hal-harness`)**: Add a 1-command bridge from `hal-decrypt` to `pace audit` & `pace classify`.
5. **Curated Multi-Agent Hubs (`kyegomez/awesome-multi-agent-papers`, `vivy-yi/awesome-agent-orchestration`, `WooooDyy/LLM-Agent-Paper-List`)**: 5-line PRs under *Evaluation & Benchmarking* + *Toolkits* linking `arXiv:2611.17610`, `mahmoudsajjadi/pace`, and `sajjadi/pace-studio`.

---

## 2. Five Related-Work Citation Templates (For Authors)

1. **Why a greedy baseline is insufficient:**
   > Comparisons of multi-agent systems against a single greedy pass confound inter-agent communication with independent sample multiplicity and additional test-time compute; sampled noncommunicating baselines are therefore needed before attributing gains to coordination \citep{sajjadi2026more}.
2. **How to size a token-equivalent sampling pool:**
   > Under the previous-round-message accounting protocol, the token-equivalent independent-sample pool is $k_{\mathrm{tok}}=KT+(T-1)K(K-1)r$, where $r=\ell/(c_p+\ell)$; this is protocol-dependent and should be checked against logged token counts \citep{sajjadi2026more}.
3. **Why compute parity is multidimensional:**
   > Compute matching for multi-agent evaluation should report thinking tokens, total tokens, monetary cost, execution latency, independent sample count, and external tool or verifier calls, because equality on one resource dimension does not imply equality on the others \citep{sajjadi2026more}.
4. **The directional baseline rule:**
   > A noncommunicating baseline that uses no more of the declared resources and matches or exceeds a multi-agent system can rule out a positive frontier gap, whereas outperforming a weaker baseline does not establish superiority over the best feasible noncommunicating policy \citep{sajjadi2026more}.
5. **When partitioned evidence or verification may matter:**
   > Communication has a potential information advantage when agents hold complementary evidence, but $I(Y;X_j\mid X_{\mathrm{shared}},X_i)>0$ is necessary rather than sufficient; when the proposed mechanism is error correction, verifier access must also be matched across communicating and noncommunicating arms \citep{sajjadi2026more}.

---

## 3. AI Newsletter & Research Curator Pitches

* **Pitch A (Empirical reversal — Import AI / Ahead of AI):**
  > Across five studies that report both greedy and sampled single-agent baselines, replacing the greedy comparator with a sampled baseline shifts the multi-agent accuracy difference by −0.038 on average (318 paired contrasts across 72 unique cells). In Choi et al.'s 14 model-benchmark configurations, greedy accuracy is 0.670, five-sample majority voting reaches 0.747, and five-agent debate reaches 0.715: the apparent +0.045 gain over greedy becomes −0.031 against voting. Paper: https://arxiv.org/abs/2611.17610 | Interactive Studio: https://huggingface.co/spaces/sajjadi/pace-studio
* **Pitch B (Practitioner engineering — Latent Space / The Batch):**
  > PACE defines a protocol-specific token-equivalent sample-pool size, $k_{\mathrm{tok}}=KT+(T-1)K(K-1)r$, and documents Expert MAS on SMFR at 96.51% accuracy ($555) versus 57.0% for five-sample CoT-SC and 20.2%–63.0% for automated multi-agent topologies—attributing the gain to domain workflow engineering and verification affordances rather than unverified peer conversation alone (`arXiv:2611.17610`, `github.com/mahmoudsajjadi/pace`).
* **Pitch C (Reproducibility / methodology):**
  > PACE separates four baseline rungs (greedy, sampled, budget-matched, Pareto frontier) and audits six resources (thinking tokens, total tokens, cost, latency, sample count, external tool/verifier calls), paired with a 7-field Evaluation Card and 6-item reviewer checklist (`arXiv:2611.17610`).

---

## 4. Five-Slide Journal-Club Deck Blueprint

1. **Slide 1 — A single-pass baseline does not isolate coordination** (*Figure 1: The Baseline Ladder*)
2. **Slide 2 — Baseline choice changes the measured gap** (*Figure 5 & Table 2*)
3. **Slide 3 — The pooled result is negative, but not universal** (*Table 3: Exploratory REML Model*)
4. **Slide 4 — Controlled experiment: frontier gains and placebo checks** (*Figure 6, Table 5, Table 6*)
5. **Slide 5 — Conditions that can justify coordination are structural** (*Figure 7: Failure Channels and Escape Routes*)

---

## 5. Open Challenges Post (GitHub Discussions / alphaXiv)

1. **Challenge 1 — Heterogeneous cross-model debate** (must beat a noncommunicating mixed-model ensemble of the exact same model pool).
2. **Challenge 2 — Sandboxed tool-use agents and external verification** (must give identical filesystem, test runner, and verifier permissions to single-agent baselines).
3. **Challenge 3 — Larger and frontier reasoning models** (replicate shared vs. partitioned evidence above 8B, logging reasoning tokens separately).
4. **Challenge 4 — Adaptive early stopping and compute allocation** (report per-item token distributions and tail latency against adaptive noncommunicating sampling).
