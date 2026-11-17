# CME Resource-Accounting Schema & Data Dictionary

**Specification Version:** 1.0.0 (JSON-Schema Aligned)  
**Author:** Seyed Mahmoud Sajjadi Mohammadabadi  
**Date:** November 2026  

---

## 1. Overview & Architectural Relationship to IETF "Agent Run Metrics"

In October 2026, the IETF published an Internet-Draft titled *"Agent Run Metrics"* proposing a preliminary JSON interchange format for logging AI agent executions. 

### Relationship to the IETF Draft:
- **Overlap:** Both formats record total input tokens, output tokens, wall-clock latency, and basic invocation counts.
- **What CME Adds Beyond the IETF Draft:**
  1. **Scaffold vs. Productive Reasoning Distinction:** CME explicitly isolates reasoning/scratchpad tokens ($R_{\text{reason}}$) from prompt repetition, role headers, and echoed chat histories ($R_{\text{scaffold}}$).
  2. **Three-State Data Provenance:** Every metric in CME requires an explicit provenance tag (`measured`, `estimated`, or `unavailable`). Estimates are never masked as physical measurements.
  3. **Concurrency & Serialized Latency Accounting:** Distinguishes between the arithmetic sum of individual API latencies and the end-to-end serialized critical-path latency.
  4. **Baseline Parity Assertions:** CME provides native schema fields for pairing multi-agent telemetry against a declared single-agent control arm.

---

## 2. Two-Tier Telemetry Architecture

Telemetry is captured at two hierarchical levels:
1. **Model-Call Level (`CallRecord`):** Logged on every discrete LLM generation or tool execution.
2. **Run Level (`RunManifest`):** Aggregated summary representing the complete problem-solving attempt.

### 2.1 Model-Call Level Schema (`CallRecord`)

```json
{
  "call_id": "call_a1_round1_001",
  "run_id": "run_gsm8k_item_42_mas",
  "agent_id": "agent_proposer_1",
  "role": "mathematician",
  "parent_call_id": null,
  "model": "meta-llama/Llama-3.1-8B-Instruct",
  "provider": "vllm_local",
  "start_time": 1731189400.125,
  "end_time": 1731189402.450,
  "latency_seconds": 2.325,
  "tokens": {
    "prompt_tokens": 420,
    "completion_tokens": 280,
    "reasoning_tokens": 190,
    "scaffold_tokens": 230,
    "provenance": {
      "prompt": "measured",
      "completion": "measured",
      "reasoning": "measured",
      "scaffold": "measured"
    }
  },
  "cost_usd": 0.000185,
  "cost_provenance": "estimated_standard_rate",
  "tool_calls_count": 0,
  "retries_count": 0,
  "status": "success"
}
```

### 2.2 Run-Level Schema (`RunManifest`)

```json
{
  "run_id": "run_gsm8k_item_42_mas",
  "experiment_id": "exp_phase3_debate_evaluation",
  "task_id": "gsm8k_test_item_42",
  "method_name": "3_agent_debate_2_rounds",
  "architecture_type": "multi_agent_debate",
  "agent_count": 3,
  "rounds_count": 2,
  "total_calls": 6,
  "resource_vector": {
    "r_reason": 1140,
    "r_token": 4200,
    "r_cost": 0.00285,
    "r_lat": 6.85,
    "r_sample": 6,
    "r_sys": 0
  },
  "scaffold_metrics": {
    "total_scaffold_tokens": 2100,
    "scaffold_percentage": 50.0
  },
  "concurrency": {
    "sum_call_latency": 13.95,
    "end_to_end_wall_clock_latency": 6.85,
    "parallelism_speedup_ratio": 2.03
  },
  "outcome": {
    "predicted_answer": "42",
    "ground_truth": "42",
    "is_correct": true
  }
}
```

---

## 3. Strict Aggregation & Non-Double-Counting Rules

1. **Tokens:** $R_{\text{token}} = \sum (\text{prompt\_tokens} + \text{completion\_tokens})$ across all calls.
2. **Reasoning Tokens:** $R_{\text{reason}} = \sum \text{reasoning\_tokens}$. If reasoning tokens are not reported by the model provider, status must be set to `unavailable`.
3. **Latency:**
   - **Sum Latency:** $\sum \text{latency\_seconds}$ (measures raw compute duration).
   - **Serialized Latency ($R_{\text{lat}}$):** $\max(\text{end\_time}) - \min(\text{start\_time})$ along the critical execution path.
4. **Scaffolding:** Non-reasoning overhead includes repeated system prompts, formatting instructions, and echoed prior-round messages.
   $$\text{Scaffold Percentage} = \frac{R_{\text{scaffold}}}{R_{\text{token}}} \times 100\%$$

---

## 4. Data Dictionary

| Field | Type | Unit | Description | Status Options |
| :--- | :--- | :--- | :--- | :--- |
| `r_reason` | float | tokens | Tokens generated within internal scratchpads/thinking blocks | `measured`, `estimated`, `unavailable` |
| `r_token` | float | tokens | Total prompt and completion tokens consumed | `measured` |
| `r_cost` | float | USD (\$) | Monetary cost computed from billed rate or standard pricing | `measured`, `estimated` |
| `r_lat` | float | seconds | End-to-end serialized elapsed wall-clock time | `measured` |
| `r_sample` | integer | count | Total stochastic forward passes drawn | `measured` |
| `r_sys` | integer | count | Number of external tool invocations (bash, compilers, search) | `measured` |
