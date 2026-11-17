# Experimental Protocol

## 1. Goal

This protocol defines the live open-weight evaluation of multi-agent and single-agent reasoning under controlled resource regimes. It is designed for local evaluation with open-weight models through Ollama and includes a deterministic mock fallback when a model endpoint is unavailable.

The protocol is intended for measurement and audit. It does not treat synthetic runs as evidence about real model behavior.

## 2. Model registry

The evaluated model families are selected from open-weight checkpoints accessible through Ollama. The protocol allows the following families when present locally:

- Qwen
- Gemma
- Llama

The protocol requires model identifiers, quantization settings, and context length to be logged for every run.

## 3. Local execution environment

The evaluation is run locally with a command-line workflow. The required endpoint is:

- http://localhost:11434/api/generate

If the local endpoint is unavailable, the protocol uses a deterministic mock model and flags the result as fallback-based.

## 4. Problem set

The default benchmark subset is a GSM8K-style arithmetic reasoning subset. The protocol uses 50 to 100 items, with a fixed seed for reproducible sampling.

Each item contains:

- a question string
- a canonical final answer
- a benchmark name
- an item index

The item subset is logged in a manifest so each run can be reproduced.

## 5. Conditions

The protocol evaluates three conditions for each item:

### 5.1 Single greedy

- temperature: 0.0
- one model call
- one final answer
- binary correctness logged per item

### 5.2 Majority vote

- temperature: 0.7
- five independent samples
- majority answer is selected
- item-level binary correctness logged after majority aggregation

### 5.3 Three-round debate

- five agents
- three rounds of discussion
- each round produces a provisional answer
- the final answer is selected by majority vote or by a deterministic selector when necessary
- binary correctness logged per item

A placebo-message ablation is included as a control. In this condition, agents receive irrelevant or content-free messages of matched length. It tests whether communication gains reflect actual content exchange or merely increased token volume.

## 6. Prompt format

The protocol uses a neutral prompt template for each condition. The template includes a short instruction, the question, and a response format that encourages a final numeric answer.

Example format:

```text
Solve the problem carefully. Give only the final answer.
Question: {question}
Answer:
```

The debate prompt adds an instruction to critique and revise the current answer while preserving the original question and the prior round summary.

## 7. Seed schedule

Each condition is evaluated under a fixed schedule:

- seed 1: pilot tuning
- seed 7: main calibration subset
- seed 42: fixed reproducibility seed

The protocol logs the seed used for each run, and all random draws are recorded in the run manifest.

## 8. Temperature settings

- greedy: 0.0
- sampled majority vote: 0.7
- debate: 0.7
- placebo-message condition: 0.7

This keeps the non-communicating and communication conditions comparable while preserving realistic stochastic variation.

## 9. Output logging

For every item and condition, the protocol logs:

- question identifier
- condition label
- model identifier
- generated answer
- canonical answer
- correctness indicator
- total token count
- reasoning token count
- latency

The per-item binary vectors are then used to compute correlations and comparative metrics.

## 10. Statistical summary

The primary correlation metric is the empirical Pearson phi between binary correctness vectors from the same item set:

$$
\hat{\phi} = \frac{\sum_i (y_i^{(1)} - \bar{y}^{(1)})(y_i^{(2)} - \bar{y}^{(2)})}{\sqrt{\sum_i (y_i^{(1)} - \bar{y}^{(1)})^2 \sum_i (y_i^{(2)} - \bar{y}^{(2)})^2}}.
$$

The protocol records the phi values for:

- single greedy vs. debate
- majority vote vs. debate
- single greedy vs. majority vote

A valid estimate must satisfy $-1 \le \hat{\phi} \le 1$.

## 11. Fallback rule

If the local Ollama endpoint is unavailable or returns an error, the protocol runs the deterministic mock model and records:

- fallback_used = true
- model identifier
- mock mode flag
- reason for fallback

The fallback result is retained for software validation, but it is not treated as evidence about a real model behavior.

## 12. Acceptance criteria

The protocol is considered complete when:

1. all three conditions run on the same item subset,
2. binary vectors are logged for each item,
3. phi values are computed and checked against $[-1, 1]$,
4. the output manifest includes both the local model configuration and the fallback status,
5. the run can be reproduced from the item manifest and the logged seed.

## 13. Summary

This protocol isolates a central measurement: whether the same questions are solved by a single model, independent sampling, and communication, and whether the paired correctness patterns are aligned or divergent. The strict requirement is not simply accuracy, but measurement under a properly declared regime with item-level binary logging.
