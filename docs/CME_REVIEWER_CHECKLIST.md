# The CME Reviewer Checklist: Evaluation Standards for Multi-Agent LLM Systems
**The Compute-Matched Evaluation (CME) Standard for Peer Review**  
*Recommended for NeurIPS, ICML, ICLR, AAAI, and Nature Machine Intelligence*

---

## 1. Executive Summary for Reviewers and Area Chairs

A widespread flaw in empirical evaluations of Multi-Agent Systems (MAS) is the **Unmatched Compute Confound**: an $N$-agent system communicating over $T$ interaction rounds is compared against a single agent executing a single greedy forward pass ($N=1, T=1$). Because the multi-agent system receives $\mathcal{O}(N \times T)$ times the inference tokens, prompt calls, and monetary budget, any reported performance gains reflect simple **test-time compute scaling and repeated sampling** (ensembling), rather than communicative coordination.

This checklist establishes standard verification criteria to determine whether an empirical submission makes a methodologically valid claim of multi-agent superiority.

---

## 2. The 6-Point Reviewer Evaluation Rubric

Every submission claiming that a multi-agent architecture outperforms a single-agent baseline must satisfy the following six evaluation criteria:

### Criterion 1: Specification of the 6D Resource-Accounting Vector
The paper must explicitly report its resource-accounting vector:
$$\mathbf{R} = \langle R_{\text{reason}}, R_{\text{token}}, R_{\text{cost}}, R_{\text{lat}}, R_{\text{sample}}, R_{\text{sys}} \rangle$$
- **$R_{\text{reason}}$ (Thinking Tokens):** Tokens consumed within reasoning/scratchpad blocks across all calls.
- **$R_{\text{token}}$ (Total Tokens):** Cumulative input, output, system, and scaffold tokens.
- **$R_{\text{cost}}$ (Monetary Cost):** Financial cost based on provider API pricing or normalized FLOPs.
- **$R_{\text{lat}}$ (Wall-Clock Concurrency Latency):** Cumulative serial response time including multi-round synchronization delays.
- **$R_{\text{sample}}$ (Sample / Instance Count):** Number of model generations drawn and aggregated.
- **$R_{\text{sys}}$ (System Scaffolding & Tool Calls):** Total API invocations, external search queries, and verifier executions.

*Reviewer Question:* Does the paper explicitly state which dimension of $\mathbf{R}$ is strictly controlled, approximately matched, or unmatched?

### Criterion 2: Parity with Single-Agent Scaling Baselines (No Strawmen)
A greedy single-agent baseline ($K=1$) is **strictly insufficient** to establish multi-agent superiority.
- When $R_{\text{sample}} > 1$ (e.g., $N$ agents): The baseline must include **Self-Consistency (CoT-SC)** or **Majority Voting** with an equal number of samples $K=N$.
- When $R_{\text{token}}$ or $R_{\text{cost}}$ is scaled: The single-agent baseline must be allocated an equal budget via extended Chain-of-Thought (e.g., test-time thinking token expansion or Best-of-$N$ search).

*Reviewer Question:* Does the multi-agent system beat single-agent Self-Consistency / Best-of-$N$ under equivalent sample or token budgets?

### Criterion 3: Complete Accounting of Scaffolding & Context Echoing Overhead
Multi-agent protocols incur severe token overhead from repeated system prompts, role descriptions, and echoed communication histories.
- All non-reasoning scaffold tokens ($C_{\text{scaffold}}$) must be deducted from the total compute budget.
- Papers must report the ratio of productive reasoning tokens to scaffold overhead.

*Reviewer Question:* Did the authors conceal prompt and history token overhead, or deduct them transparently from the multi-agent system's effective compute budget?

### Criterion 4: Rigorous Sample Size & Item-Level Dispersion Reporting
Point-estimate accuracy comparisons without dispersion metrics are unacceptable.
- Authors must report the test benchmark sample size ($N_{\text{items}}$) and number of independent evaluation runs ($m$).
- Standard errors, confidence intervals, or per-instance binary item correctness must be provided to enable paired McNemar or log-odds tests.
- Benchmarks with $N < 100$ items (e.g., small subsets of SWE-bench) must be explicitly flagged as exploratory.

*Reviewer Question:* Are sample sizes and paired variance statistics provided for all evaluation benchmarks?

### Criterion 5: Task Decomposability & Verification Grounding Disclosure
Returns from multi-agent coordination are heavily dependent on task structure:
- **Decomposable Tasks:** Problems with naturally parallel subtasks (e.g., multifaceted financial analysis) allow specialization.
- **Sequential Deduction:** Multi-hop reasoning tasks (e.g., FRAMES, MuSiQue) suffer severe degradation under debate due to context dilution and echoed hallucinations.
- **External Verifiers:** Papers claiming coordination gains must disclose whether agents communicate with each other (unverified peer debate) or interact with ground-truth external verifiers (unit tests, compilers, retrieval engines).

*Reviewer Question:* Does the paper characterize task decomposability and test whether single agents with the same verifier achieve identical gains?

### Criterion 6: Full Disclosure of Architecture Search & Negative Results
Frameworks that search across agent topologies (e.g., AFlow, ADAS, MAS-Zero) explore dozens of candidate graphs.
- Authors must report the cumulative compute cost of the architecture search phase.
- All evaluated architectures, including failing configurations, must be tabulated to prevent selective reporting bias.

*Reviewer Question:* Is the architecture search budget accounted for, and are negative configurations transparently reported?

---

## 3. Recommended Reviewer Decisions

| Reviewer Finding | Recommended Verdict |
|:---|:---|
| Multi-agent system beats greedy single agent, but trails or matches CoT-SC / Best-of-$N$ at equal budget | **Weak Reject / Reject** (Confounded by ensembling) |
| Multi-agent system scales tokens/cost by $>5\times$ without reporting budget-matched single-agent curves | **Reject** (Strawman baseline) |
| Multi-agent system beats single-agent search under strictly matched thinking tokens or Pareto frontier | **Accept / Strong Accept** (Genuine coordination efficiency) |
| Multi-agent system succeeds on tool-partitioned task with ground-truth verifiers, with full 6D vector | **Strong Accept** (Valid architectural contribution) |
