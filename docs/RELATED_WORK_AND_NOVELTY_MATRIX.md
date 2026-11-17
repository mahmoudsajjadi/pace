# Related Work & Novelty Matrix (Phase 1 Deliverable)

**Date:** November 10, 2026  
**Repository:** `Automation/01_Research/Manuscripts/01_pure_ml_reasoning_and_test_time_compute`  
**Purpose:** Rigorous, uninflated prior-art comparison across 14 direct/indirect papers and 6 evaluation platforms to precisely delineate novelty without claiming invalid "firsts".

---

## 1. Prior-Art Analysis: 14 Direct & Indirect Empirical Papers

| Study | Primary Contribution | Baseline Used | Resource Constraint Enforced | Finding on MAS vs Baseline | Key Limitation / Gap Addressed by Our Work |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Kapoor et al. (2024)** *AI Agents That Matter* | Evaluated agents under cost constraints on SWE-bench/WebArena. | Greedy single-agent & basic retries. | Monetary dollar cost. | MAS often exceeds cost of equivalent single-agent runs. | Focuses on agentic environments (SWE-bench), not multi-agent reasoning topologies; does not provide formal decomposition of communication vs sampling. |
| **Wang et al. (EMNLP 2024)** *Reasoning in Token Economies* | Studied token allocation across reasoning steps and agents. | Single-agent CoT with varying token lengths. | Total token budget. | Single agents with matched tokens frequently match debate. | Data reported primarily in charts; did not provide cell-level machine-readable data; limited to 2 model families. |
| **Li et al. (TMLR 2024)** *More Agents Is All You Need* | Demonstrated performance scaling with agent count via sampling. | Single-pass greedy. | Number of agents/samples (not tokens/cost). | More agents improve performance via majority voting. | Conflates sampling benefits (best-of-N) with inter-agent communication; lacks matched-compute single-agent controls. |
| **Tran & Kiela (2024/2025)** | Evaluated multi-agent debate against sequential reasoning at equal test-time tokens. | Single-agent extended reasoning (CoT-SC). | Generated thinking tokens strictly matched. | Single-agent reasoning matches or exceeds debate at equal tokens. | Restricted to mathematical reasoning (GSM8K, MATH); assumes monotonic single-agent context utilization without testing context-partitioned tasks. |
| **Jwalapuram et al. (2024)** *Illusion of Multi-Agent Advantage* | Paired multi-agent debate against self-consistency baselines. | CoT-SC ($k=3, 5, 8$). | Generation sample count matched; tokens/cost unconstrained. | Debate advantage disappears or turns negative against SC. | Evaluated sample counts ($k$), leaving median MAS cost 1.6× higher; did not formalize resource vector or Pareto frontier. |
| **Smit et al. (2024)** | Investigated consensus mechanisms and majority voting in multi-LLM setups. | Single-agent greedy & majority voting. | Prompt iterations. | Voting drives majority of agreement gains. | Did not isolate inter-agent communication messages from independent response aggregation. |
| **Zhang et al. (2024)** | Compared diverse multi-agent communication topologies. | Single-agent CoT. | Unconstrained (MAS uses substantially more compute). | Complex topologies beat single agents. | Vulnerable to Baseline Distortion: compares heavy multi-agent setups against $N=1$ greedy pass. |
| **Yang et al. (2024)** | Evaluated multi-agent debate vs self-consistency on reasoning benchmarks. | 16-sample CoT-SC. | Fixed 16 generations across all methods. | CoT-SC matches debate on most reasoning tasks. | Treats 16 generations as equivalent compute without accounting for inter-agent prompt token accumulation. |
| **Wunderlich et al. (ACL 2026 SRW)** | Benchmarked debate and Mixture-of-Agents (MoA) under equal compute budgets. | Best-of-N and self-consistency. | Matched total floating-point / generation budget. | **Positive:** Debate (+1.3) and MoA (+2.7) beat SC on MMLU-Pro under matched budgets. | Evaluated specific multi-model configurations; focused on benchmark scores without establishing a general attribution metric ($\Gamma$). |
| **Ferreira et al. (2026)** *Beyond Symmetric Agents* | Tested heterogeneous agent configurations under fixed budget. | Heterogeneous single-model samples. | Matched token budget. | Heterogeneous teams offer gains only when individual model capabilities are complementary. | Does not isolate the pure marginal effect of communication from ensemble diversity. |
| **Bertalanic & Fortuna (2026)** *Cost of Consensus* | Analyzed communication overhead and Ringelmann effects in LLM groups. | Independent voting ensemble. | Total message count. | Communication leads to groupthink and diminishing returns beyond 3 agents. | Examines team dynamics but lacks a standardized resource accounting framework and schema. |
| **Nguyen et al. (2026)** *Think More or Read More* | Investigated trade-off between internal reasoning tokens and external communication. | Single-agent deep thinking (R1-style). | Equal total test-time tokens. | Single-agent deep thinking dominates debate on formal logic. | Restricted to reasoning models; does not explore task structures where information is partitioned. |
| **Ann et al. (2026)** *The Interaction Tax* | Quantified token overhead spent on protocol syntax and message passing. | Non-communicating parallel workers. | Total generated tokens. | Communication tax consumes 25–45% of compute without proportional accuracy gains. | Focuses on token accounting without providing a full Pareto-frontier evaluation platform. |
| **Zhu et al. (2026)** *Demystifying MAD* | Analyzed message convergence and confirmation bias in multi-agent debate. | Self-refinement and CoT-SC. | Equal generation steps. | Debate often induces harmful conformity on questions where initial answers were diverse. | Limited empirical scope (2 benchmarks, proprietary models); no open evaluation toolkit. |

---

## 2. Platform & Benchmark Landscape: 6 Evaluation Platforms

| Platform / Benchmark | Target Scope | Resource Accounting Model | Non-Communicating Controls Included? | Leaderboard / Registry Dynamic | Key Distinction / Gap Addressed by Our Work |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **HAL (Holistic Agent Leaderboard, ICLR 2026)** | Broad agent evaluation across diverse environments. | Reports dollar cost per trajectory. | Basic single-pass agents only. | Living public leaderboard. | Measures agentic tool use and execution success, but does not isolate communication from sampling or enforce matched-budget baselines. |
| **TeamBench (2025/2026)** | Evaluates multi-agent collaboration on cooperative tasks. | Token counts per task. | Single-agent comparison, but not resource-matched. | Static benchmark with task-specific scores. | Introduces "Teamwork Necessity Index", but does not account for the token overhead of communication or test against Pareto-matched self-consistency. |
| **AgentWorld (2025/2026)** | Simulation environment for multi-agent social interaction. | Interaction steps. | Isolated agents in simulated sandbox. | Benchmark environment. | Measures "Causal Collaboration Effectiveness" in open-ended games, but does not address test-time compute allocation or formal reasoning benchmarks. |
| **MASBench & MAC-Bench** | Multi-agent software engineering and coordination benchmarks. | Execution turns and wall-clock time. | Single-agent baseline with standard prompts. | Static benchmarks. | Evaluates task success on complex workflows, but lacks fine-grained accounting of reasoning vs communication tokens. |
| **MASEval & MAESTRO** | Frameworks for orchestrating and evaluating multi-agent systems. | API cost logging. | Compares multi-agent frameworks against each other. | Orchestration framework. | Designed for building and deploying agents, not for rigorous scientific hypothesis testing or resource-matched attribution. |
| **Artificial Analysis (Intelligence Index v5)** | Industry-standard model benchmarking for speed, quality, and price. | High-precision latency, tokens/sec, and API pricing. | Single-agent API endpoints only. | Real-time commercial model index. | Focuses on raw model capability and provider economics; does not evaluate multi-agent orchestration, test-time scaling, or communication efficiency. |

---

## 3. Novelty Delineation: What Is Established vs What Is Novel

### A. What Is Already Established in the Literature (We Do NOT Claim Novelty Here):
1. **Multi-Agent Systems often fail against self-consistency:** Established by Jwalapuram et al. (2024), Tran & Kiela (2024), and Yang et al. (2024).
2. **Multi-Agent systems consume substantially more tokens and cost:** Established by Kapoor et al. (2024), Wang et al. (2024), and Ann et al. (2026).
3. **Voting alone accounts for substantial gains:** Established by Smit et al. (2024) and Li et al. (2024).
4. **General Agent Leaderboards exist:** HAL, TeamBench, and AgentBench already exist as public leaderboards.

### B. What Our Project Uniquely Contributes:
1. **The Formal Coordination Premium ($\Gamma$):** A mathematically grounded attribution metric that isolates the incremental value of inter-agent communication from independent sampling, test-time reasoning tokens, and sample size, anchored by the constrained single-agent Pareto frontier $f(\mathcal{B})$.
2. **Algebraic Sampling Gap Identity:** Proof that $\Delta_{\text{gap}} = p_{\text{single}} - p_{\text{sampled}}$ cancels multi-agent performance entirely, proving that reporting gains over greedy single-pass baselines measures baseline weakness rather than coordination success.
3. **Harmonized 4-Category Baseline Taxonomy (A–D):** Eliminating ambiguous "compute-matched" labels by strictly separating greedy single-pass (A), sample-matched (B), resource-matched (C), and Pareto frontier sweeps (D).
4. **Systematic 531-Contrast Evidence Registry:** The largest cross-study, cell-level audited database of multi-agent vs single-agent contrasts, complete with provenance coordinates and resource-matching audit statuses.
5. **Open, Reusable CME Evaluation Toolkit (`mae_eval`):** Standardized JSON schema, multi-dimensional parity auditor, and trace logging for communication, reasoning, and token overhead.
6. **Task-Structure Boundary Identification:** Demonstrating where communication is genuinely beneficial (context-partitioned, sequential dependency) versus where it imposes a net tax (independent formal reasoning).
