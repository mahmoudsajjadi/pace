# The Author's Quickstart Guide to CME Compliance
**How to Satisfy the Compute-Matched Evaluation (CME) Standards in Under 15 Minutes**

---

## 1. Why CME Compliance Helps Your Paper Get Accepted

Reviewers at NeurIPS, ICLR, ICML, and TMLR are increasingly vigilant regarding the **Unmatched Compute Confound**:
> *"The multi-agent system uses 5 agents and 3 rounds of communication, but the baseline is only a single greedy call. The reported gain is simply test-time compute scaling."*

If your paper compares a multi-agent system against a single greedy LLM, **you are at high risk of a Weak Reject or Reject score**.

Complying with the CME Checklist accomplishes two goals:
1. **Defends your paper:** Proves to reviewers that your comparisons are scientifically fair and that gains are not an artifact of uncredited sampling.
2. **Standardizes your reporting:** Provides an objective LaTeX table for your appendix that answers reviewer skepticism upfront.

---

## 2. The 15-Minute Compliance Workflow

### Step 1: Install `mae-eval` (1 minute)
```bash
pip install mae-eval
```

### Step 2: Choose Your Compute Control Strategy (5 minutes)
Depending on your task domain, match at least **one** primary compute constraint:

| If Your Setup Scales... | Match This Single-Agent Baseline: | CME State |
| :--- | :--- | :--- |
| **Agent Count ($N$ agents)** | **Self-Consistency (CoT-SC)** with $K = N$ samples | `Strictly Controlled` ($R_{\text{sample}}$) |
| **Thinking / Scratchpad Tokens** | **Extended Thinking Tokens** (e.g., $1\text{k}\to 8\text{k}$ tokens) | `Strictly Controlled` ($R_{\text{reason}}$) |
| **Total Prompt & Completion Tokens** | **Best-of-$N$** or **Iterative Refinement** at equal tokens | `Approximately Matched` ($R_{\text{token}}$) |
| **Monetary API Cost ($ USD)** | **Cost-Matched Sampling** or Pareto Frontier Curve | `Unmatched (Measured)` ($R_{\text{cost}}$) |

> **Crucial Rule:** If your compute is *unmatched* (e.g., exploring an expensive automated framework), **that is acceptable!** Simply classify that dimension as `Unmatched (Measured)` in the resource vector $\mathbf{R}$ and discuss it transparently. Transparency prevents reviewer rejection.

### Step 3: Run the Audit CLI & Export LaTeX (5 minutes)
Log your generation traces to a JSONL file and run:
```bash
mae-eval audit --log my_traces.jsonl --export-latex cme_table.tex
```
This generates a publication-ready LaTeX table documenting your 6D resource vector:
$$\mathbf{R} = \langle R_{\text{reason}}, R_{\text{token}}, R_{\text{cost}}, R_{\text{lat}}, R_{\text{sample}}, R_{\text{sys}} \rangle$$

### Step 4: Drop the Table into Your Appendix (4 minutes)
Include `\input{cme_table}` in your submission appendix and check **"Yes"** on the conference OpenReview CME submission form.

---

## 3. How to Answer the 6 Checklist Questions

### Q1: Resource Vector $\mathbf{R}$ Specification
- **Good Answer:** *"We report the full 6D resource vector in Table 3 of the appendix. Thinking tokens and sample count are strictly controlled ($K=5$); latency and dollar costs are measured and reported."*
- **What to Avoid:** Leaving token counts or execution latency unmeasured.

### Q2: Equal-Compute Baselines
- **Good Answer:** *"In addition to greedy chain-of-thought, we evaluate a single-agent baseline using self-consistency with five samples (CoT-SC, K=5) and budget-matched extended thinking tokens."*
- **What to Avoid:** Comparing exclusively against single greedy $T=0.0$ generation.

### Q3: Scaffolding and Context Echoing Overhead
- **Good Answer:** *"System prompts, agent persona headers, and echoed chat histories accounted for 32% of total tokens and were explicitly deducted from the effective reasoning token budget."*
- **What to Avoid:** Counting prompt repetition as 'reasoning tokens'.

### Q4: Sample Rigor & Dispersion
- **Good Answer:** *"We evaluate on the full test sets of GSM8K ($N=1319$) and HumanEval ($N=164$). We report paired McNemar test p-values and 95% bootstrap confidence intervals across three seeds."*
- **What to Avoid:** Testing on $N=20$ instances without reporting confidence intervals or significance tests.

### Q5: Task Decomposability & Ground-Truth Verifiers
- **Good Answer:** *"Tasks with parallel execution (financial multi-query retrieval) showed positive gains; tasks with sequential logic suffered context degradation. Both single-agent and multi-agent systems were given identical access to the bash execution tool."*
- **What to Avoid:** Giving the multi-agent system tools (e.g., web search) while denying them to the single-agent baseline.

### Q6: Architecture Search Disclosure
- **Good Answer:** *"We evaluated four fixed topologies (Centralized, Debate, Sequential, Independent). No automated architecture search was performed."* (Or: *"Architecture search evaluated 18 candidate graphs consuming $4.2 \times 10^6$ tokens, documented in Appendix D."*)
- **What to Avoid:** Hiding failed architectures and only publishing the cherry-picked winning graph.

---

## 4. Example LaTeX Table for Submission Appendices

```latex
\begin{table}[h]
\centering
\small
\caption{\textbf{CME Resource Accounting Vector $\mathbf{R}$ across Experimental Arms.}}
\begin{tabular}{lcccccc}
\toprule
System Arm & $R_{\text{reason}}$ & $R_{\text{token}}$ & $R_{\text{cost}}$ & $R_{\text{lat}}$ & $R_{\text{sample}}$ & $R_{\text{sys}}$ \\
\midrule
Single Greedy (CoT)   & 512 tok  & 850 tok   & \$0.001 & 1.2 s & 1 & 0 tools \\
Single CoT-SC ($K=5$) & 2,560 tok & 4,250 tok & \$0.005 & 1.3 s & 5 & 0 tools \\
Multi-Agent Debate ($N=5$) & 2,560 tok & 7,800 tok & \$0.009 & 4.8 s & 5 & 0 tools \\
\midrule
\textbf{CME Control State} & \textit{Controlled} & \textit{Unmatched} & \textit{Audited} & \textit{Unmatched} & \textit{Controlled} & \textit{Matched} \\
\bottomrule
\end{tabular}
\end{table}
```
*Including this single table in your appendix satisfies the CME Checklist and preempts the most common baseline critique in peer review.*
