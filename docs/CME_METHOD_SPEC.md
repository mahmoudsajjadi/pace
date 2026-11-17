# Compute-Matched Evaluation (CME): Methodological Specification & Fair-Comparison Protocol

**Author:** Seyed Mahmoud Sajjadi Mohammadabadi  
**Affiliation:** Department of Computer Science and Engineering, University of Nevada, Reno  
**Contact:** `mahmoud.sajjadi@unr.edu`  
**Version:** 1.0 (Operational Protocol Specification)  
**Date:** November 2026  

---

## 1. The Three Connected Components of the CME Framework

Rather than presenting a standalone checklist, CME is structured as a three-tier scientific architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Component A: Resource-Accounting Specification       │
│  Standardized, machine-readable record of exact resources consumed     │
│  at both the individual model-call level and complete run level.       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Component B: Fair-Comparison Protocol                │
│  Methodological rules for declaring primary matching constraints and   │
│  evaluating multi-agent systems against strong single-agent baselines. │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Component C: Executable Evaluation Toolkit           │
│  Open-source software (`mae-eval`) that ingests telemetry, validates   │
│  parity assertions, and generates reproducible Pareto analyses.        │
└────────────────────────────────────────────────────────────────────────┘
```

The 6-point Reviewer Checklist is simply the **simplest human-readable interface** to this underlying protocol.

---

## 2. Operational Definitions: Separating Concepts

To prevent methodological ambiguity, CME formally defines five distinct concepts that are often conflated in agent literature:

1. **Resource Measurement:** The objective recording of physical or computational quantities consumed during execution ($R_{\text{reason}}, R_{\text{token}}, R_{\text{cost}}, R_{\text{lat}}, R_{\text{sample}}, R_{\text{sys}}$). Measurements must distinguish directly observed values from estimates.
2. **Budget Matching:** An experimental design condition wherein two or more systems are allocated identical or bounded amounts of a declared target resource.
3. **Coordination Attribution:** The scientific claim that a performance difference $\Delta = p_{\text{MAS}} - p_{\text{SAS}}$ arises from multi-agent communication, division of labor, or debate, rather than differences in test-time compute or sample multiplicity.
4. **Performance-Resource Trade-off (Pareto Analysis):** The empirical curve tracing task accuracy as a function of increasing resource expenditure across different architectures.
5. **Practical Deployment Decisions:** Applied heuristics determining whether an organization should adopt a multi-agent pipeline based on context-window constraints, sandboxing requirements, or execution latency limits.

---

## 3. The Multidimensional Matching Framework

No two systems can match every resource dimension simultaneously. For instance, concurrent multi-agent architectures may match wall-clock latency while consuming $5\times$ the tokens, or match total tokens while increasing execution rounds and serialized latency.

Under CME, **every empirical comparison must declare its Primary Matching Constraint** and report the remaining dimensions as secondary outcomes:

| Primary Constraint | Research Question Addressed | Single-Agent Baseline Requirement | Secondary Dimensions Monitored |
| :--- | :--- | :--- | :--- |
| **Equal Generated Tokens** | Does communicative coordination improve generation efficiency over single-model thinking? | Extended thinking tokens / extended reasoning traces | $R_{\text{cost}}, R_{\text{lat}}, R_{\text{sample}}$ |
| **Equal Total Monetary Cost** | For a fixed dollar expenditure, do multiple communicating calls beat repeated single calls? | Cost-matched sampling (Best-of-$N$ or CoT-SC matched to MAS dollar cost) | $R_{\text{token}}, R_{\text{lat}}, R_{\text{sample}}$ |
| **Equal Execution Latency** | Under hard serialized response-time deadlines, does parallel agent decomposition help? | Single greedy or parallel independent sampling ($K$ parallel calls) | $R_{\text{token}}, R_{\text{cost}}$ |
| **Equal Independent Samples** | Does communicative debate outperform independent stochastic variance reduction? | Self-Consistency (CoT-SC) with $K = N$ samples | $R_{\text{token}}, R_{\text{cost}}, R_{\text{lat}}$ |
| **Equal Model Invocations** | Does topological message passing matter when forward pass count is controlled? | Iterative single-agent self-refinement ($T$ rounds) | $R_{\text{token}}, R_{\text{reason}}$ |

---

## 4. Requirement for Strong Single-Agent Baselines

A comparison against a single greedy forward pass ($K=1, T=0.0$) is **never sufficient** to establish multi-agent superiority if the multi-agent system uses multiple samples, rounds, or expanded tokens.

### The Mandatory Baseline Rule:
- If a multi-agent system draws $N$ candidate solutions: compare against **CoT-SC ($K=N$)**.
- If a multi-agent system consumes $B$ reasoning tokens: compare against **single-agent thinking tokens budget $B$**.
- If a multi-agent system costs $\$C$: compare against **single-agent test-time search costing $\$C$**.

---

## 5. Pareto Frontier Analysis Over Single-Point Claims

Rather than declaring a single "winner" at an arbitrary compute budget, CME encourages evaluating systems along their **performance-resource Pareto frontier**.

Let a system configuration be defined by accuracy $p \in [0, 1]$ and resource vector $\mathbf{R} \in \mathbb{R}_{\ge 0}^6$.
A multi-agent configuration strictly Pareto dominates single-agent scaling if and only if:
$$(p_{\text{MAS}} \ge p_{\text{SAS}}) \;\land\; (\mathbf{R}_{\text{MAS}} \le \mathbf{R}_{\text{SAS}}) \;\land\; \big[(p_{\text{MAS}} > p_{\text{SAS}}) \lor (\mathbf{R}_{\text{MAS}} < \mathbf{R}_{\text{SAS}})\big]$$

Where systems are Pareto-incomparable (e.g., MAS achieves higher accuracy at higher cost), the report must present the cost-accuracy curve rather than asserting unconstrained superiority.

---

## 6. Baseline Tiers and the Sampling gap (added 2026-11-10)

Headline comparisons in the paper are reported by baseline type, because a pooled mean mixes baselines of different strength.

- **Tier A (single-pass baseline):** the single-agent baseline is one greedy pass or one run (for example a plain CoT row, a single agent, or a CoT agent).
- **Tier B (sampled or budget-matched baseline):** the baseline receives several samples (CoT-SC, self-consistency with 16 samples) or the same thinking-token or budget allowance as the multi-agent system.
- **Sampling gap:** for the same multi-agent arm, benchmark and model, the difference in the multi-agent delta between Tier B and Tier A: `gap = (p_MAS - p_SAS,B) - (p_MAS - p_SAS,A)`. It is defined only for studies that report both baselines (Jwalapuram, Zhang, Smit, Ke in the current corpus).
- **Caveat for the Jwalapuram et al. CoT-SC row:** the source describes its CoT and CoT-SC rows as "the best observed score across MAS system entries"; per-entry scores are not published, so the row is an upper-bound single-agent baseline.
- Studies with extreme influence are shown with and without them (Zhang et al. supplies 180 of 531 contrasts). Wunderlich et al. is excluded from the tiers because its multi-agent arm is itself self-consistency.

Implementation: `analysis/run_baseline_tiers.py` (outputs `outputs/baseline_tiers.json`, `outputs/baseline_tier_contrasts.csv`).
