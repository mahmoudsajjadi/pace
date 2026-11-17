# Comprehensive Specification: Coordination Evaluation Platform, CME Toolkit & Gold-Standard Roadmap

**Project Title (Frozen):** *"More Agents, More Samples, or More Thinking? Untangling Coordination, Sampling, and Test-Time Compute in Multi-Agent LLMs"*  
**Author:** Seyed Mahmoud Sajjadi Mohammadabadi (`mahmoud.sajjadi@unr.edu`), University of Nevada, Reno  
**Target Venue:** *Transactions on Machine Learning Research* (TMLR) — Evaluation & Methodology Track (Target Submission: ~January 10, 2027) / Major ML/NLP Venues (ICLR, NeurIPS, ACL)  

---

## Executive Summary

This document establishes the master architectural specification to elevate the research into a field-defining, highly cited gold standard for multi-agent LLM evaluation. Rather than presenting a narrow negative finding that multi-agent systems trail single agents under matched compute, this project delivers the **canonical methodology, formal metric ("Coordination Premium"), open-source evaluation platform, and empirical benchmark** that future multi-agent researchers must cite to substantiate their claims:

> *"A reported advantage of multi-agent systems should not be attributed to coordination unless it survives comparison against the strongest non-communicating baseline under explicitly declared resource constraints."*

The platform comprises:
1. **Mathematical Formalism:** The **Coordination Premium** $\Gamma(\mathcal{B}, t, m)$ and constrained single-agent frontier $f(\mathcal{B}; t, m)$.
2. **Systematic Literature Protocol:** PRISMA-compliant search across 2023--Nov 2026, plot digitization for chart-only studies, and cell-level audit ledgers.
3. **Factorial Experimental Design:** Testing 4 task structures, 5 open-weight models (runnable locally on an RTX 4070 12GB VRAM via Ollama) and commercial APIs, 6 architectures, and 4 budget regimes.
4. **Reproducible Tooling (`mae_eval` / `cme_toolkit`):** Standardized JSON/YAML evidence schema, live telemetry tracker, parity auditor, and automatic report generator.
5. **Open Science & Anonymized Governance:** Compliance with TMLR double-blind requirements during review, transitioning to a public Zenodo DOI, CITATION.cff, and community leaderboard post-acceptance.

---

## 1. Novelty Claim and Terminology: The "Coordination Premium"

### 1.1 Definition & Formalization
The **Coordination Premium** ($\Gamma$) quantifies the marginal performance improvement attributable strictly to inter-agent communication above an equal-compute non-communicating baseline:

$$\Gamma(\mathcal{B}; t, m) \;\triangleq\; \mathbb{E}\big[\operatorname{Accuracy}(\pi_{\text{comm}}^*; t, m)\big] \;-\; f(\mathcal{B}; t, m)$$

Where:
- $\mathcal{B} \subseteq \mathbb{R}_+^6$: Explicitly declared resource budget vector (thinking tokens, total tokens, monetary cost, execution latency, sample count, tool calls).
- $t$: Task type and structure (decomposability, sequential dependency, context partitioning).
- $m$: Model family and baseline competence.
- $\pi_{\text{comm}}^*$: Optimal communicating multi-agent architecture satisfying $\mathbb{E}[\mathbf{R}(\pi_{\text{comm}}^*)] \preceq \mathcal{B}$.
- $f(\mathcal{B}; t, m) \triangleq \sup_{\pi \in \Pi_{\text{SA}}: \mathbb{E}[\mathbf{R}(\pi)] \preceq \mathcal{B}} \mathbb{E}[\operatorname{Accuracy}(\pi; t, m)]$: Constrained single-agent frontier under budget $\mathcal{B}$.

### 1.2 Pairwise Formulation (Eliminating Winner's Curse)
To avoid selection bias and unequal tuning effort across architectures, empirical comparisons report the **Pairwise Coordination Delta**:

$$\Delta_{\text{comm}}(\pi_{\text{comm}}, \pi_{\text{indep}}; \mathcal{B}, t, m) \;\triangleq\; \mathbb{E}\big[\operatorname{Accuracy}(\pi_{\text{comm}}; t, m)\big] \;-\; \mathbb{E}\big[\operatorname{Accuracy}(\pi_{\text{indep}}; t, m)\big]$$

subject to $\mathbb{E}[\mathbf{R}(\pi_{\text{comm}})] \preceq \mathcal{B}$ and $\mathbb{E}[\mathbf{R}(\pi_{\text{indep}})] \preceq \mathcal{B}$, explicitly naming the matched resource (token-matched, cost-matched, or sample-matched).

### 1.3 Baseline-Strengthening Identity
When comparing against greedy ($p_{B_0}$) and sampled ($p_{\text{sampled}}$) baselines, the sampling gap satisfies:

$$\Delta_{\text{gap}} \;\triangleq\; (p_{\text{MAS}} - p_{\text{sampled}}) - (p_{\text{MAS}} - p_{B_0}) \;=\; p_{B_0} - p_{\text{sampled}}$$

Because multi-agent performance $p_{\text{MAS}}$ cancels algebraically, $\Delta_{\text{gap}}$ directly measures baseline strengthening via variance reduction, proving that reported multi-agent advantages drop primarily because the baseline was reinforced.

---

## 2. Systematic Literature Search & Plot Digitization Protocol

### 2.1 Coverage & Query Strategy (2023 -- Nov 10, 2026)
- **Databases:** arXiv (cs.AI, cs.CL, cs.MA), ACL Anthology, OpenReview, Semantic Scholar, OpenAlex, Crossref, IEEE Xplore, PMLR.
- **Search Queries:**
  - `"multi-agent debate self-consistency"`
  - `"LLM agent evaluation cost compute"`
  - `"chain-of-thought vs multi-agent reasoning"`
  - `"LLM reasoning token budget"`
  - `"compute-matched agent evaluation"`
  - `"test-time compute scaling multi-agent"`
- **Inclusion Criteria:** Studies comparing communicating multi-agent systems with single-agent or independent-sampling baselines, or evaluating multi-agent test-time compute.
- **Exclusion Criteria:** Purely theoretical papers without empirical evaluation; single-agent tool pipelines without inter-agent communication.

### 2.2 Plot Digitization Protocol
Studies reporting compute-accuracy frontiers only via charts (e.g., Wang et al., EMNLP 2024, *Reasoning in Token Economies*) are not excluded. Instead:
1. Vector graphics / PDF charts are extracted and digitized using in-code coordinate parsers and WebPlotDigitizer.
2. Extracted coordinates are recorded with explicit measurement error bounds ($\pm \epsilon$) and reported as a dedicated sensitivity tier alongside exact tabular data.

### 2.3 Comprehensive Novelty Mapping vs. 14 Key Competitors

| Reference (Year) | Contribution & Findings | Our Contribution / Novelty Gap Filled |
| :--- | :--- | :--- |
| **Wang et al. (EMNLP 2024)** | Budget-aware evaluation; CoT-SC outperforms debate when compute is matched. | Digitizes plot data; formalizes multi-dimensional $\mathbf{R}$; generalizes beyond math to multi-domain task taxonomy. |
| **Kapoor et al. (2024)** | *AI Agents That Matter*: cost-controlled agent evaluation on code and QA. | Extends beyond single-agent tool wrappers to interactive multi-agent debate, MoA, and communication topologies. |
| **Li et al. (TMLR 2024)** | *More Agents Is All You Need*: Agent Forest shows sampling + voting scales with agent count. | Proves that sample multiplicity explains apparent agent scaling; isolates communication gains beyond voting. |
| **Smit et al. (2024)** | Benchmarking MAD strategies; debate $\le$ self-consistency unless hyper-tuned. | Harmonizes cross-paper evidence; applies multi-level meta-analysis across disparate matching regimes. |
| **Zhang et al. (2025)** | Stop Overvaluing Multi-Agent Debate: 5 debate methods, 9 benchmarks, 4 model families. | Disentangles greedy baselines from sampled baselines across 180 contrasts; establishes the baseline ladder. |
| **Yang et al. (2025)** | Revisiting MAD as test-time scaling; conditional effectiveness on hard tasks. | Evaluates under fixed-generation caps (16 samples) and incorporates multi-dimensional resource accounting. |
| **Tran & Kiela (2026)** | Fixed reasoning tokens on multihop QA; single agent matches/beats debate (DPI argument). | Extends beyond DPI assumptions to model context crowding ($B_{\text{eff}}$), tool scaffolding, and non-token resources. |
| **Jwalapuram et al. (2026)** | *The Illusion of Multi-Agent Advantage*: auto-MAS costs 10$\times$ CoT-SC; expert MAS succeeds. | Tabulates dual baselines (greedy CoT and CoT-SC Table 4); resolves cost ratio ($8.1\times$ vs CoT, $1.6\times$ vs CoT-SC). |
| **Wunderlich et al. (ACL 2026)** | Equal compute on MMLU-Pro: debate (+1.3%) and MoA (+2.7%) beat self-consistency. | Confirms positive evidence boundary condition: collaborative gains emerge on dense multiple-choice knowledge tasks. |
| **Ferreira et al. (Sept 2026)** | *Beyond Symmetric Agents*: 23 models, 5,500+ runs; generation-budget matched voting ties debate. | Uncovers context-window overflow hazards; integrates strict context truncation monitoring into CME protocol. |
| **Bertalanič & Fortuna (Apr 2026)** | *The Cost of Consensus*: debate uses 2.1–3.4$\times$ tokens; consensus collapse. | Adopts the **Noise Placebo Control** to separate semantic communication from token volume. |
| **Bertalanič & Fortuna (2026)** | *The Ringelmann Effect in Multi-Agent LLMs*: nominal agent scaling shows coordination decay. | Connects social choice team-size scaling laws to LLM agent coordination efficiency. |
| **Nguyen, Gupta, Le (Oct 2026)** | *Think More or Read More?*: self-consistency matches/beats debate in 93% of settings. | Validates shared-context token-budget theory across diverse open-weight model architectures. |
| **Ann, Liu, Tan (Aug 2026)** | *The Interaction Tax*: 11 verifier-scored tasks show interaction is an expensive default. | Formalizes communication overhead accounting within the CME reporting card. |

---

## 3. Factorial Experimental Design

### 3.1 Task-Structure Taxonomy
Tasks are classified across four structural categories to evaluate conditional effectiveness:
1. **Independent Parallel Tasks:** Subtasks are separable and concurrently solvable (e.g., parallel multi-document analysis, batch code linting). *Hypothesis: $\Gamma > 0$ under latency constraints.*
2. **Sequential Multi-Step Deduction:** Downstream reasoning strictly depends on upstream steps (GSM8K, MATH, PlanCraft). *Hypothesis: $\Gamma \le 0$ due to error cascade and context crowding.*
3. **Context-Partitioned Retrieval:** Information is distributed across disjoint environments or large document corpora (HotPotQA, BrowseComp-Plus). *Hypothesis: $\Gamma > 0$ when context exceeds single-model windows.*
4. **Independent Tool-Use Tasks:** Diverse external tools operated concurrently (HumanEval with test execution, multi-API querying). *Hypothesis: Tool access explains gains, not conversational prompting.*

### 3.2 Model Families & Local Open-Weight Suite
Experiments evaluate both proprietary APIs and local open-weight models runnable on consumer hardware (NVIDIA RTX 4070, 12 GB VRAM) via Ollama (4-bit quantization, 8K context limit):

| Model Checkpoint | Family / Parameter Size | License | Role in Experimental Design |
| :--- | :--- | :--- | :--- |
| **Qwen3.5-9B** | Qwen (9B) | Apache 2.0 | Primary open-weight general-purpose backbone |
| **Gemma 4 12B** | Google (12B) | Apache 2.0 | Cross-family architectural replication |
| **Ministral 3 8B** | Mistral (8B) | Apache 2.0 | Agent-oriented instruction-tuned model |
| **Llama 3.1 8B Instruct** | Meta (8B) | Llama Community | Established community baseline |
| **DeepSeek-R1-Distill-Qwen-7B**| DeepSeek (7B) | MIT | Reasoning-specialized RL-distilled baseline |
| **GPT-4o / GPT-4.5** | OpenAI | Commercial API | High-capability proprietary anchor |
| **Gemini 2.5 Pro** | Google | Commercial API | Long-context multimodal anchor |

### 3.3 Evaluated Architectures & Controls
For each model and task, six architectures are evaluated under identical prompts and seeds:
1. **Single-Agent Greedy CoT:** Conventional baseline ($N=1, T=1$).
2. **Single-Agent Self-Consistency (SAS-SC):** $k$ independent samples with majority voting.
3. **Single-Agent Self-Refinement:** Sequential multi-turn revision without peer agents.
4. **Multi-Agent Debate (MAS-Debate):** $N \in \{3, 5\}$ agents communicating across $T \in \{1, 2, 3\}$ rounds.
5. **Multi-Agent Consensus (Agent Forest):** Independent agents without communication, aggregated by majority voting.
6. **Noise Placebo Control:** Agents receive irrelevant or content-free peer messages of equal token length to isolate semantic communication from token volume.

### 3.4 Budget Regimes
1. **Equal Calls Budget:** Fixed number of LLM invocations ($N_{\text{calls}} \le C$).
2. **Equal Tokens Budget:** Fixed sum of input, output, and reasoning tokens ($R_{\text{token}} \le B$).
3. **Equal Cost Budget:** Fixed dollar expenditure based on published API pricing ($R_{\text{cost}} \le \$X$).
4. **Equal Latency Budget:** Fixed wall-clock execution ceiling ($R_{\text{lat}} \le L$ seconds).

---

## 4. Statistical Analysis & Preregistration Protocol

1. **Hierarchical Mixed-Effects Logistic Regression:**
   $$\operatorname{logit}\big(P(Y_{ijk} = 1)\big) = \beta_0 + \beta_{\text{arch}} \cdot X_{ijk} + u_{\text{task}(i)} + v_{\text{model}(j)} + w_{\text{instance}(k)}$$
   Accounts for random variations across tasks, models, and instances.
2. **Paired Instance-Level Tests:** McNemar's test for binary correctness on identical prompt splits; paired $t$-tests on batch accuracy.
3. **Empirical Correlation Measurement ($\phi$):** Measure instance-level question correlation on held-out calibration splits rather than assuming synthetic values ($\phi = 0.50$).
4. **Cluster-Robust Inference:** Cluster-robust standard errors (CR2) adjusting for small study degrees of freedom.
5. **Multiplicity Adjustment:** Benjamini-Hochberg False Discovery Rate (FDR) applied across all confirmatory hypotheses.
6. **Preregistration:** Complete experimental protocol, hypotheses, analysis scripts, and seed lists preregistered on the Open Science Framework (OSF).

---

## 5. CME Reusable Tooling & Evidence Registry Schema

### 5.1 Machine-Readable Evidence Schema (`schema.json`)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CMEEvaluationRecord",
  "type": "object",
  "required": ["task_id", "architecture", "model", "budget", "resources", "metrics"],
  "properties": {
    "task_id": {"type": "string"},
    "task_type": {"type": "string", "enum": ["independent_parallel", "sequential_deduction", "context_partitioned", "independent_tools"]},
    "architecture": {
      "type": "object",
      "required": ["name", "category", "num_agents", "rounds"],
      "properties": {
        "name": {"type": "string"},
        "category": {"type": "string", "enum": ["single_greedy", "sample_matched", "resource_matched", "pareto_frontier"]},
        "num_agents": {"type": "integer"},
        "rounds": {"type": "integer"},
        "is_placebo": {"type": "boolean"}
      }
    },
    "model": {
      "type": "object",
      "required": ["model_id", "family", "quantization"],
      "properties": {
        "model_id": {"type": "string"},
        "family": {"type": "string"},
        "quantization": {"type": "string"}
      }
    },
    "budget": {
      "type": "object",
      "required": ["mode", "value"],
      "properties": {
        "mode": {"type": "string", "enum": ["tokens", "calls", "cost_usd", "latency_sec"]},
        "value": {"type": "number"}
      }
    },
    "resources": {
      "type": "object",
      "required": ["thinking_tokens", "total_tokens", "cost_usd", "latency_sec", "calls"],
      "properties": {
        "thinking_tokens": {"type": "integer"},
        "total_tokens": {"type": "integer"},
        "cost_usd": {"type": "number"},
        "latency_sec": {"type": "number"},
        "calls": {"type": "integer"},
        "tool_calls": {"type": "integer"}
      }
    },
    "metrics": {
      "type": "object",
      "required": ["correct", "score"],
      "properties": {
        "correct": {"type": "boolean"},
        "score": {"type": "number"},
        "coordination_premium": {"type": "number"}
      }
    }
  }
}
```

### 5.2 Python Package Components (`mae_eval` / `cme_toolkit`)
- **`tracker.py` (`ResourceTracker`):** Instruments model invocations, logging input/output/reasoning tokens, API costs, and latency.
- **`auditor.py` (`ParityAuditor`):** Evaluates declared resource constraints and flags unmatched dimensions (`strictly_controlled`, `approximately_controlled`, `unmatched`, `unreported`, `not_applicable`).
- **`report.py` (`EvaluationReport`):** Automatically produces terminal summaries, machine-readable JSON exports, and publication-ready LaTeX tables.
- **`cli.py`:** Command-line interface for running parity checks: `mae-eval audit run.json --baseline baseline.json`.

---

## 6. Implementation Timeline & Venues

```
Phase 1: Manuscript Claim Corrections & Section 3 Theory Overhaul (COMPLETED - Commit 83f6805)
Phase 2: Systematic Search & Plot Digitization (Nov 10 – Nov 24, 2026)
Phase 3: Cell-Level Verification & Driver Study Audit (Nov 24 – Dec 8, 2026)
Phase 4: Open-Weight Ollama Factorial Experiment (Dec 8 – Dec 22, 2026)
Phase 5: Final Submission Build & CAC Reviewer Card (Dec 22, 2026 – Jan 10, 2027)
Post-Review: Public Zenodo DOI, Community Leaderboard & Open PR Platform (Q1/Q2 2027)
```
