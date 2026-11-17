# Scientific Framework

## 1. Objective

This document defines the core estimands used in the compute-matched evaluation of multi-agent and single-agent language models. The goal is to separate three effects that are commonly conflated in the literature: coordination, sample multiplicity, and inference-time compute.

The target paper title is fixed: "More Agents, More Samples, or More Thinking? Untangling Coordination, Ensembling, and Test-Time Compute in Multi-Agent LLMs".

## 2. Resource vector

For a model run $\pi$ on task $t$ and model $m$, define the six-dimensional resource vector:

$$
\mathbf{R}(\pi; t, m) = \langle R_{\text{reason}}, R_{\text{token}}, R_{\text{cost}}, R_{\text{lat}}, R_{\text{sample}}, R_{\text{sys}} \rangle.
$$

Each component reports one resource axis:

- $R_{\text{reason}}$: generated reasoning tokens or scratchpad tokens.
- $R_{\text{token}}$: total prompt, completion, and scaffold tokens.
- $R_{\text{cost}}$: monetary cost or budget-normalized compute cost.
- $R_{\text{lat}}$: end-to-end latency, including serialized waits and tool calls.
- $R_{\text{sample}}$: the number of independent generation samples or replicates.
- $R_{\text{sys}}$: scaffolding overhead, tools, retrieval calls, or verifier operations.

Because $\mathbf{R}$ is multi-dimensional, comparisons are defined by a declared constraint set $\mathcal{B} \subseteq \mathbb{R}_+^6$ rather than by a single scalar budget.

## 3. Constrained single-agent frontier

Let $\Pi_{\text{SA}}$ be the space of single-agent policies. Define the constrained single-agent frontier as:

$$
f(\mathcal{B}; t, m) \triangleq \sup_{\pi \in \Pi_{\text{SA}}, \mathbb{E}[\mathbf{R}(\pi)] \preceq \mathcal{B}} \mathbb{E}[\text{Accuracy}(\pi; t, m)].
$$

This quantity is the best observed or theoretically achievable single-agent accuracy under a declared resource constraint $\mathcal{B}$. In practice, $f(\mathcal{B}; t, m)$ is usually approximated by a specific baseline policy or by a measured frontier sweep.

The frontier is not an unconditional benchmark of all possible models. It is a budget-conditioned reference point that makes the comparison explicit.

## 4. Coordination premium

For a communicating policy $\pi_{\text{comm}}$ and a non-communicating baseline $\pi_{\text{indep}}$, define the pairwise coordination delta:

$$
\Delta_{\text{comm}}(\pi_{\text{comm}}, \pi_{\text{indep}}; \mathcal{B}, t, m)
=\mathbb{E}[\text{Accuracy}(\pi_{\text{comm}}; t, m)] - \mathbb{E}[\text{Accuracy}(\pi_{\text{indep}}; t, m)],
$$

subject to the resource constraints

$$
\mathbb{E}[\mathbf{R}(\pi_{\text{comm}})] \preceq \mathcal{B},\quad
\mathbb{E}[\mathbf{R}(\pi_{\text{indep}})] \preceq \mathcal{B}.
$$

The coordination premium is the best communicating policy minus the best non-communicating policy under the same declared budget:

$$
\Gamma(\mathcal{B}; t, m) \triangleq \sup_{\pi_{\text{comm}} \in \Pi_{\text{comm}}} \mathbb{E}[\text{Accuracy}(\pi_{\text{comm}}; t, m)] - \sup_{\pi_{\text{indep}} \in \Pi_{\text{indep}}} \mathbb{E}[\text{Accuracy}(\pi_{\text{indep}}; t, m)],
$$

with both suprema taken over policies subject to $\mathbb{E}[\mathbf{R}] \preceq \mathcal{B}$.

This term is used only after the corresponding resource constraint is named. The phrase "communication premium" is not treated as a free causal conclusion when agent count, reasoning tokens, or cost were not controlled.

## 5. Additive decomposition and the sampling-gap identity

Let $p_{\text{MAS}}$ denote multi-agent accuracy, $p_{\text{single}}$ denote a single greedy baseline, and $p_{\text{sampled}}$ denote a sampled non-communicating baseline such as self-consistency or majority voting over independent samples.

The observed comparison against a single greedy baseline decomposes as:

$$
 p_{\text{MAS}} - p_{\text{single}}
=\underbrace{(p_{\text{MAS}} - f(\mathcal{B}))}_{\text{coordination term}}
+\underbrace{(f(\mathcal{B}) - p_{\text{single}})}_{\text{compute-strengthening term}}.
$$

The sampling gap compares the improvement over a sampled baseline to the improvement over a greedy baseline:

$$
\Delta_{\text{gap}}
\triangleq (p_{\text{MAS}} - p_{\text{sampled}}) - (p_{\text{MAS}} - p_{\text{single}}).
$$

Algebraically,

$$
\Delta_{\text{gap}} = p_{\text{single}} - p_{\text{sampled}}.
$$

This identity cancels the multi-agent term. Therefore, any reported sampling gap is a statement about the strengthening of the baseline, not a direct causal estimate of communication value. It is an accounting identity rather than a mechanistic effect.

## 6. Baseline taxonomy

The project uses four categories to avoid ambiguous labels.

### Category A (Greedy Single-Pass)

The comparison uses a single forward pass with no repeated sampling or communication.

### Category B (Sampled Baseline)

The reference is a non-communicating sampled baseline, such as majority voting over $k$ independent samples, but the resource budget is not strictly equalized across all dimensions.

### Category C (Resource-Matched Baseline)

The same resource constraint is applied across compared systems, such as equal reasoning tokens, equal total tokens, matched cost, or matched latency.

### Category D (Pareto Frontier Sweep)

The comparison is made across a range of resource settings and reported along an empirical Pareto frontier.

This taxonomy prevents the phrase "compute-matched" from being used unless the relevant resource dimensions were actually matched and reported.

## 7. Interpretation rules

1. A communication gain is only attributable to coordination if it survives comparison against the strongest non-communicating baseline under a declared resource budget.
2. A result that compares a multi-agent system to a single greedy pass is a Category A result and cannot be interpreted as a communication-only effect.
3. A result that compares a multi-agent system to a sampled baseline is a Category B result and may reflect sample multiplicity rather than coordination.
4. Category C and D comparisons are the primary evidence for coordination claims when the objective is to separate communication from compute.

## 8. Summary

The core empirical principle is concise:

> A reported advantage of multi-agent systems should not be attributed to coordination unless it remains after the strongest non-communicating baseline is matched on the declared resources and the resource vector is reported.
