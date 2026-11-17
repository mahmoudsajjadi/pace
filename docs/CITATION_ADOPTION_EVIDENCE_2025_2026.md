# Evidence-Based Citation & Adoption Research: Analysis of 2025–2026 Empirical ML Literature

**Author:** Seyed Mahmoud Sajjadi Mohammadabadi  
**Affiliation:** Department of Computer Science and Engineering, University of Nevada, Reno  
**Contact:** `mahmoud.sajjadi@unr.edu`  
**Date:** November 2026  
**Document Status:** Grounded Bibliometric Analysis & Literature Survey  

---

## 1. Executive Summary & Methodological Framing

A common failure mode in academic planning is treating citation counts as controllable engineering milestones or projecting exponential compounding curves (e.g., "6,000+ citations by 2035") based on aggressive interpretations of past checklists. 

In reality, academic citation in machine learning follows heavy-tailed, power-law dynamics dictated by **reusable utility**, not promotional campaigns or compliance mandates.

This document examines papers from 2025–2026 across foundation models, reasoning, test-time compute, agent platforms, and benchmarking to extract the mechanisms that drive genuine adoption.

---

## 2. Empirical Case Studies (2025–2026 Benchmarking & Systems Uptake)

### 2.1 The Case Studies Landscape

The table below records dated snapshots of high-uptake papers across relevant domains. Notice that citation databases disagree substantially due to differing deduplication, preprint merging, and crawling algorithms.

| Paper Title & Lead Authors | Focus Domain | Primary Artifact Released | Semantic Scholar (Oct 21, 2026) | OpenAlex (Oct 21, 2026) | Citations / Month | Primary Citation Mode |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Qwen3 Technical Report** (Qwen Team, Alibaba) | Foundation Models | Weights, Code, Base/Instruct Models | 9,442 | 147 | ~780 | Method / Foundation Model Reuse |
| **DeepSeek-R1** (DeepSeek-AI) | Test-Time Reasoning / RL | Open Weights, Distillations, Training Recipe | 6,092 | 539 | ~670 | Model Artifact / Reasoning Baseline |
| **DAPO: Open-Source LLM RL System at Scale** | Systems / Alignment | Scalable Open RL Training Codebase | 3,007 | 16 | ~330 | Software / Training Pipeline Reuse |
| **OpenHands: Platform for AI Software Developers** (Wang et al., 2025) | Agent Architecture / Systems | Permissive Platform, 13 Task Adapters | 340 | 85 | ~28 | Software Infrastructure / Benchmark Harness |
| **Evaluation and Benchmarking of LLM Agents: A Survey** | Benchmarking / Taxonomies | 2D Taxonomy of Agent Capabilities | 161* | 42 | ~14 | Survey / Background Framing |
| **The Illusion of Thinking** | Test-Time Compute / Reasoning | Controlled Complexity Tasks, Traces | 72* | 19 | ~8 | Methodological Critique / Follow-up Experiments |
| **MultiAgentBench** | Multi-Agent Evaluation | Benchmark Suite (Collaboration/Competition) | 128 | 31 | ~11 | Benchmark Dataset Reuse |
| **Scaling LLM Test-Time Compute Optimally** (Snell et al., 2024/2025) | Test-Time Search / Compute | Formal Search Framework & Scaling Curves | 412 | 118 | ~29 | Theoretical Baseline / Scaling Framework |
| **Towards Thinking-Optimal Scaling of Test-Time Compute** (Yang et al., 2025) | Reasoning Limits | Empirical Saturation Analysis & Traces | 185 | 49 | ~15 | Empirical Baseline & Analysis |

*\*Note: Figures marked with an asterisk were retrieved from topic-specific literature maps (e.g., mlsanity / TopCited index through early November 2026) and reflect different citation indexation criteria than raw Semantic Scholar crawls.*

---

## 3. Dissecting Citation Discrepancies and Database Inconsistencies

1. **Semantic Scholar vs. OpenAlex Discrepancies:**
   - *Example:* Qwen3 shows 9,442 on Semantic Scholar vs. 147 on OpenAlex. This occurs because Semantic Scholar aggressively merges preprints, technical blog mentions, industrial reports, and ArXiv versions, whereas OpenAlex requires formal peer-reviewed or indexed DOI citations.
   - *Takeaway:* Never treat citation counts from a single database as an absolute metric of scientific truth.

2. **Citing Modes Taxonomy:**
   When analyzing how papers are actually cited in peer-reviewed literature, citations fall into seven distinct categories:
   - **Type A (Artifact / Software Reuse):** The citing paper imports the Python package or runs the model (e.g., OpenHands, `transformers`, `vllm`).
   - **Type B (Mandatory Baseline Comparison):** The citing paper evaluates their new method against this technique (e.g., CoT-SC, Best-of-$N$).
   - **Type C (Benchmark / Dataset Reuse):** The citing paper evaluates on this benchmark split (e.g., SWE-bench, GSM8K).
   - **Type D (Conceptual / Theoretical Framing):** The citing paper cites the definition or taxonomy in the introduction (e.g., 2D agent taxonomy).
   - **Type E (Superficial Background Citation):** Mentioned in a cluster of 5–10 papers in related work ("Recently, several studies explored agents [1, 2, 3, 4]...").
   - **Type F (Critique or Direct Replication):** The citing paper attempts to refute or replicate the claim.
   - **Type G (Policy / Checklist Compliance):** Citing a form or checklist.

---

## 4. Why Checklists Alone Do Not Generate Sustainable Citations

Reviewing the historical precedents reveals critical nuances:
1. **The NeurIPS Reproducibility Checklist (Pineau et al.):**
   - NeurIPS instituted a submission checklist. However, the conference guidelines specifically instructed authors *not* to cite a specific paper unless discussing checklist methodology; the checklist was built into OpenReview as an editorial mechanism. Pineau's high citation count came from her accompanying survey and empirical challenge papers, not the bureaucratic checklist itself.
2. **Dodge et al. (*Show Your Work*, EMNLP 2019):**
   - Dodge et al. did not create a mandatory conference-wide carbon tax or compliance barrier. They provided **reusable code for analyzing validation performance against compute budgets** and empirical curves showing how tuning budgets distort model rankings. Researchers cited the paper because they used the tuning curve methodology.
3. **OpenReview Customization:**
   - OpenReview allows conference administrators to add custom questions. However, Program Chairs guard the submission form aggressively against bloat. A submission question is never adopted because an outside researcher published a JSON file; it is adopted only when a consensus of Area Chairs demands it to resolve an active review crisis.

---

## 5. What a Solo-Author Evaluation Paper Can Realistically Learn

A solo academic researcher cannot release a 70B frontier foundation model or spend \$5M on pretraining. However, solo-author and small-team evaluation papers achieve major, enduring impact by providing:

1. **A Reusable Scientific Object (Not Just a PDF):**
   - *OpenHands* succeeded by giving researchers a platform they could run.
   - *CME's equivalent:* A clean, lightweight, zero-dependency Python toolkit (`mae-eval`) that any researcher can run in 30 seconds to audit their token, cost, and latency budgets.
2. **A Question that Changes How Researchers Interpret Results:**
   - *"Are we measuring multi-agent coordination, or did we just give one method $5\times$ more compute?"*
   - This simple reframing forces researchers to second-guess their own experiments before submitting.
3. **A Shared, Operational Vocabulary:**
   - Disentangling **coordination**, **stochastic sampling**, and **test-time compute** via the 6D resource vector $\mathbf{R}$.
4. **A Constructive Decision Heuristic:**
   - Instead of merely saying "multi-agent doesn't work", providing a clear diagnostic: when to scale single-agent tokens, when to use majority voting, and when to deploy multiple agents (partitioned tools, sandboxed execution).
