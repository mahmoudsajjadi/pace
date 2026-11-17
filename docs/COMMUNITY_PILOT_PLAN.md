# Community Pilot & Voluntary Benchmark Engagement Plan

**Project:** Compute-Matched Evaluation (CME) Standard  
**Author:** Seyed Mahmoud Sajjadi Mohammadabadi  
**Date:** November 2026  
**Document Status:** Community Pilot Strategy (Non-Mandatory, Utility-First)  

---

## 1. Core Philosophy: Voluntary Adoption Through Practical Utility

Mandates imposed from above create friction and resentment. The CME framework succeeds when researchers **voluntarily adopt it because it makes their research easier to design, debug, and publish**.

Our goal is to provide a tool that helps authors answer:
> *"Before I submit my multi-agent paper, how do I know if my baseline is fair and will withstand reviewer scrutiny?"*

---

## 2. The 5-Stage Adoption Progression

```
Stage 1: Internal Validation
[Passing unit tests, clean CLI install, reproducible example trace]
           │
           ▼
Stage 2: Independent Checklist Validation
[30-paper inter-rater reliability study with Krippendorff's alpha >= 0.80]
           │
           ▼
Stage 3: Community Pilot & Voluntary Challenge
[AgentEval workshop challenge: authors voluntarily submit CME telemetry]
           │
           ▼
Stage 4: Open-Source Ecosystem Integration
[Adapters for inspect_ai, lm-evaluation-harness, and OpenHands]
           │
           ▼
Stage 5: Institutional Discussion
[Presenting proven utility to journal editors and conference organizers]
```

---

## 3. The "AgentEval" Voluntary Reproducibility Challenge

Rather than asking conferences to mandate a checklist, we host a **Voluntary Reproducibility Challenge** at a top-tier workshop (NeurIPS 2027 / ICLR 2028):

### Challenge Structure:
- **Task:** Participants submit empirical evaluations of novel agent architectures or re-evaluations of existing methods.
- **Incentive:** Submissions providing verified `mae-eval` trace files compete for the **"Best Compute-Matched Evaluation Award"**.
- **Deliverables:**
  1. An open repository of paired multi-agent and single-agent traces.
  2. Concrete author feedback on where the resource-accounting schema was easy or difficult to instrument.
  3. Empirical evidence demonstrating whether the checklist was practical for outside labs.

---

## 4. Ecosystem Integration (Harness Adapters)

To minimize the effort required by external labs, we build lightweight adapters for widely used evaluation frameworks:

1. **`mae-eval-inspect`:** Adapter for UK AI Safety Institute's `inspect_ai` framework, logging token and latency telemetry automatically.
2. **`mae-eval-harness`:** Integration with EleutherAI's `lm-evaluation-harness`, allowing one-line baseline comparisons against CoT-SC.
3. **`mae-eval-openhands`:** Telemetry hook for the OpenHands platform to log software agent execution costs.

When researchers can add CME tracking with a single import:
```python
from mae_eval.adapters import record_session
```
adoption occurs naturally as part of the standard Python development workflow.
