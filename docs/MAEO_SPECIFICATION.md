# The Multi-Agent Evaluation Observatory (MAEO) Specification
**Architecture, Schemas, and Open Tooling for Standardized MAS Benchmarking**

---

## 1. Vision & Architecture

The **Multi-Agent Evaluation Observatory (MAEO)** is designed to serve as the definitive, living benchmark infrastructure for multi-agent LLM systems, establishing the standard across academic peer review, industry deployment, and scientific scaling laws.

```
+---------------------------------------------------------------------------------------+
|                                    MAEO PLATFORM                                      |
+---------------------------------------------------------------------------------------+
|  1. STANDARDIZED EVALUATION ENGINE (`mae-eval` Python Package)                        |
|     - Context & scaffold token auditing                                               |
|     - Wall-clock concurrency & serialization latency profiler                         |
|     - Provider API & FLOPs cost tracker                                               |
+---------------------------------------------------------------------------------------+
|  2. OPEN REPOSITORY & REPRODUCIBILITY VAULT                                            |
|     - Item-level binary correctness matrices ($N_{\text{item}} \times \text{Runs}$)   |
|     - Paired contrast ledgers with verified source citations                          |
|     - Immutable Zenodo archive records and versioned schema validation                |
+---------------------------------------------------------------------------------------+
|  3. INTERACTIVE LEADERBOARD & PARETO DASHBOARD                                        |
|     - Multi-dimensional Pareto frontier visualization ($R_{\text{cost}}$ vs Acc)       |
|     - Dynamic filtering by task decomposability and tool integration                   |
|     - Single-agent baseline parity checker (CoT-SC / Best-of-$N$)                     |
+---------------------------------------------------------------------------------------+
```

---

## 2. The 6-Dimensional Resource Schema (`mae_schema.json`)

All benchmark submissions to MAEO must conform to the JSON schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "MAEO Benchmark Submission Schema",
  "type": "object",
  "required": [
    "submission_metadata",
    "system_architecture",
    "benchmark_definition",
    "resource_vector",
    "evaluation_outcomes"
  ],
  "properties": {
    "submission_metadata": {
      "type": "object",
      "required": ["system_name", "authors", "publication_status", "repository_url"],
      "properties": {
        "system_name": {"type": "string"},
        "authors": {"type": "array", "items": {"type": "string"}},
        "publication_status": {"type": "string", "enum": ["Preprint", "Conference", "Journal"]},
        "doi": {"type": "string"},
        "repository_url": {"type": "string", "format": "uri"}
      }
    },
    "system_architecture": {
      "type": "object",
      "required": ["paradigm", "agent_count", "interaction_rounds", "verifier_type"],
      "properties": {
        "paradigm": {"type": "string", "enum": ["SAS", "Debate", "Sequential", "Hierarchical", "Automated_Graph"]},
        "agent_count": {"type": "integer", "minimum": 1},
        "interaction_rounds": {"type": "integer", "minimum": 1},
        "verifier_type": {"type": "string", "enum": ["None", "Peer_Agreement", "Unit_Test", "Compiler", "Retrieval"]}
      }
    },
    "resource_vector": {
      "type": "object",
      "required": ["r_reason", "r_token", "r_cost", "r_lat", "r_sample", "r_sys"],
      "properties": {
        "r_reason": {"type": "number", "description": "Total reasoning/scratchpad tokens"},
        "r_token": {"type": "number", "description": "Total prompt + completion + scaffold tokens"},
        "r_cost": {"type": "number", "description": "Total monetary inference cost (USD)"},
        "r_lat": {"type": "number", "description": "Wall-clock concurrency latency in seconds"},
        "r_sample": {"type": "integer", "description": "Total model completions drawn"},
        "r_sys": {"type": "integer", "description": "Number of tool invocations / search queries"}
      }
    },
    "evaluation_outcomes": {
      "type": "object",
      "required": ["accuracy", "n_items", "matched_baseline_type", "delta_acc"],
      "properties": {
        "accuracy": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "n_items": {"type": "integer", "minimum": 1},
        "matched_baseline_type": {"type": "string", "enum": ["CoT_Greedy", "CoT_SC", "Best_of_N", "Longer_CoT"]},
        "delta_acc": {"type": "number"}
      }
    }
  }
}
```

---

## 3. The `mae-eval` Python Audit Library

The observatory provides an open-source evaluation wrapper for automated compute accounting:

```python
import time
from mae_eval import ResourceTracker, EvaluationAuditor

# Initialize tracking context
tracker = ResourceTracker(model="gpt-5", pricing_tier="standard")

with tracker.trace() as session:
    # Execute multi-agent framework
    response = run_multi_agent_system(prompt, session)

audit = session.get_resource_vector()
print(f"Reasoning Tokens: {audit.r_reason}")
print(f"Scaffold Tokens:  {audit.r_scaffold} ({audit.scaffold_pct:.1f}% overhead)")
print(f"Wall Latency:     {audit.r_lat:.2f}s")
print(f"Dollar Cost:      ${audit.r_cost:.4f}")

# Verify against equal-budget single agent
auditor = EvaluationAuditor(session)
auditor.assert_compute_parity(tolerance=0.05)
```

---

## 4. Citation and Open Data Standards

To guarantee permanent academic indexing:
1. Every quarterly release of the MAEO database is assigned a permanent DOI via Zenodo.
2. Contributed benchmarks must provide instance-level JSONL files with binary indicator outcomes ($y_{ij} \in \{0, 1\}$) to enable cluster-robust hierarchical meta-analyses.
3. Papers utilizing MAEO must cite the CME Standard and data version.
