# Benchmark Specification

## 1. Purpose

This specification defines the evaluation tasks used to separate communication effects from sample-based and compute-based gains. The tasks are divided into four tracks that vary along the principal dimensions of decomposability, context fragmentation, sequential dependency, and verification burden.

## 2. Evaluation scope

The benchmark is designed for open-weight models run locally with Ollama or a deterministic mock fallback. The primary tracking variables are accuracy, item-level correctness, total tokens, reasoning tokens, latency, sample count, and tool-use overhead.

The benchmark is not a leaderboard. It is a measurement protocol for resource-matched attribution.

## 3. Track 1: Independent Reasoning

### Definition

Tasks are solved by a single agent or a set of independent agents without strong dependencies across subproblems. This track serves as a negative-control for coordination claims.

### Examples

- arithmetic reasoning problems
- short-form grade-school word problems
- closed-form multiple-choice reasoning items

### Input format

Each item includes:

- an integer item identifier
- a prompt string
- a canonical final answer
- the benchmark name and split

### Output format

Each run returns:

- a final answer string
- whether the answer matches the canonical answer
- the total generated tokens
- the number of model calls
- the resource vector $\mathbf{R}$

### Baselines

- greedy single-agent pass
- independent five-sample majority vote
- resource-matched single agent with equal token budget

### Primary metric

- accuracy over items

### Secondary metrics

- mean tokens per correct answer
- latency per item
- calibration under repeated runs

## 4. Track 2: Sequential Tool Scaffolding

### Definition

Tasks require ordered steps, tool calls, or staged execution. These tasks often reward decomposition and verification but are sensitive to context growth and message echoing.

### Examples

- tool use with sequential steps
- constrained action planning
- multi-step code synthesis with test feedback

### Input format

Each item includes:

- the task description
- tool availability and constraints
- an optional verifier or reward signal
- the expected final product or answer

### Output format

Each run returns:

- tool invocation trace
- step-by-step state transitions
- final state or answer
- step cost and latency

### Baselines

- single-agent sequential planning
- independent sampling with majority vote
- debate with communication turned off
- placebo-message control condition

### Primary metric

- success rate on task completion

### Secondary metrics

- mean tool calls per task
- average steps to completion
- verification rate before final answer

## 5. Track 3: Context-Partitioned Verification

### Definition

Tasks require multiple partial views of the same problem or a verifier that checks intermediate content. This track is the most relevant to communication claims in distributed reasoning.

### Examples

- verification benchmarks with distinct contexts
- partitioned logic problems
- tasks where independent agents inspect different evidence fragments

### Input format

Each item includes:

- a primary question
- context partitions or evidence slices
- an optional answer schema

### Output format

Each run returns:

- a set of local judgments
- a final synthesis decision
- per-agent agreement statistics

### Baselines

- single-agent reasoning over the full context
- sampled single-agent reasoning with the same number of draws
- communication-off ablation

### Primary metric

- answer correctness on the final decision

### Secondary metrics

- agreement among agents
- verification error rate
- marginal benefit of communication beyond independent sampling

## 6. Track 4: Long-Horizon Execution

### Definition

Tasks require many steps, extended state tracking, and repeated decisions. More context and more communication tokens can dilute the usable reasoning budget.

### Examples

- extended planning tasks
- long-form synthesis workflows
- multi-turn tool pipelines

### Input format

Each item includes:

- initial goal state
- constraints and guardrails
- available tools or APIs
- environment state

### Output format

Each run returns:

- final state
- executed steps
- final success or failure
- end-to-end cost and latency

### Baselines

- single-agent long-horizon execution
- repeated sampled single-agent baselines
- debate with communication disabled

### Primary metric

- task success rate

### Secondary metrics

- time to completion
- number of failed intermediate steps
- token efficiency per successful task

## 7. Non-communicating baselines

The benchmark must include at least one non-communicating baseline for every communication condition. A valid comparison must report the following:

1. single greedy baseline
2. independent sampled baseline at the same number of draws
3. resource-matched single-agent baseline on the declared dimensions
4. communication-off ablation where possible

The communication effect is not treated as identified unless the non-communicating controls are presented in the same budget regime.

## 8. Metrics

The benchmark reports the following metrics for every condition and task track:

- accuracy
- exact-match or task success rate
- per-item binary correctness vector
- total token usage
- reasoning token usage
- cost
- latency
- sample count
- tool calls
- communication overhead

The analysis uses per-item binary vectors so that paired comparisons can be computed directly.

## 9. Data logging requirements

Each benchmark run must log:

- model identifier and checksum or digest
- benchmark and split
- random seed
- prompt template
- decoding settings
- number of rounds
- number of agents
- total tokens and reasoning tokens
- completion status and errors
- verification status of resource matching

## 10. Summary

The four task tracks are designed to isolate the conditions under which communication is useful. Short independent tasks use a negative-control structure; sequential tasks test scaffolding overhead; context-partitioned tasks test information sharing; long-horizon tasks test state and token management. The key rule is invariant: no coordination claim is accepted without the corresponding non-communicating baseline under the same declared resource constraints.
