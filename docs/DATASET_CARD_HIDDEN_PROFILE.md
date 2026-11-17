# Dataset card: hidden-profile split-evidence control (v1)

Status: staged for archiving, not published. No Hugging Face or Zenodo upload has been made, no DOI exists, and the licence below is a proposal for the author to confirm.

## Summary

A synthetic multiple-choice task in which the evidence needed for the answer is split across five agents. A single agent shown all evidence can compute the answer. An agent shown one view can compute only a wrong answer, so independent voting over views has no route to the correct answer, and recovery requires that agents exchange what they see. It is a positive control for communication in multi-agent evaluations: if a method claims a coordination benefit, it should detect one here.

File: `data/hidden_profile/hidden_profile_v1_seed42_n500.jsonl` (500 items, SHA-256 `ece9fa74072e118317d29d4b60018f3773adbb0e8275715743d94be5c0fd4d7f`). Generator: `hidden_profile()` in `code/cme/tasks.py`; export and property checks: `scripts/export_hidden_profile.py`. The confirmatory runs use the first 200 items (same generator, seed 42).

## Motivation

The design follows the hidden-profile paradigm of Stasser and Titus (1985), in which each group member holds some shared and some unshared information and the best choice is visible only when the unshared information is pooled. In their studies groups tended to discuss shared information more than unshared information. Here the shared information favours a decoy and the pooled information favours the target. Reference: Stasser, G., and Titus, W. (1985). Pooling of unshared information in group decision making: Biased information sampling during discussion. *Journal of Personality and Social Psychology*, 48(6), 1467–1478, doi:10.1037/0022-3514.48.6.1467 (Crossref record checked 2026-11-12).

This task tests whether a pipeline can detect communication that is needed by construction. It does not show that communication helps on natural tasks, and the items are arithmetic over a table, so a positive result does not generalise to open-ended reasoning.

## Item schema

One JSON object per line:

| Field | Type | Meaning |
|---|---|---|
| `id` | string | `hp0000` … `hp0499` |
| `prompt_full_evidence` | string | the committee instructions and all 40 scores (4 candidates × 10 criteria); the question is "Which candidate has the highest total over all 10 criteria? Give the name." |
| `views` | list of 5 strings | the agent-specific prompts: same instructions, 4 shared criteria plus 2 of the 6 split criteria, and a sentence that other members see the other criteria |
| `gold` | string | the answer key: the candidate with the highest total over all 10 criteria (`Avery`, `Blake`, `Casey` or `Drew`) |
| `totals` | object | each candidate's full-evidence total |
| `synthetic` | bool | always true |

## Generation and split-evidence partition

Seed 42. Four candidates (Avery, Blake, Casey, Drew) are scored 1 to 5 on 10 equally weighted criteria. A target and a decoy candidate are drawn at random. Scores of the two other candidates are random from 2 to 3 on every criterion (capped at 3). Criteria 1 to 4 are shared: the decoy scores 5 and the target scores 2 on each. Criteria 5 to 10 are split: the target scores 5 and the decoy scores 2 on each. An item is kept only if the highest full-evidence total is unique and belongs to the target. Over all ten criteria the target totals 4 × 2 + 6 × 5 = 38 and the decoy 4 × 5 + 6 × 2 = 32. In a view with the four shared criteria and two split criteria the decoy totals 4 × 5 + 2 × 2 = 24 and the target 4 × 2 + 2 × 5 = 18, so the decoy leads by 6 in every view; the other two candidates total at most 18 in a view.

The six split criteria are shuffled per item. With agents numbered 1 to 5, agent *a* sees the criteria at positions 2*a* − 1 and 2*a* of that order, wrapping around after position 6. Agents 1, 2 and 3 see disjoint pairs that together cover all six split criteria; agents 4 and 5 repeat the pairs of agents 1 and 2. In every item two split criteria are held by exactly one agent (the pair at positions 5 and 6, agent 3) and four by two agents, so recovery of the full total requires agent 3's contribution.

## Properties verified by script (500 items, no model involved)

| Property | Violations |
|---|---|
| P1 the gold candidate has the unique highest full-evidence total | 0 of 500 |
| P2 in every one of the 2,500 views, the candidate with the highest visible total is not the gold candidate | 0 of 2,500 |
| P3 every view contains the four shared criteria and exactly two split criteria | 0 of 2,500 |
| P4 the views jointly cover at least four of the six split criteria | 0 of 500 (all 500 items cover all six; two criteria have one holder, four have two) |

Gold distribution: Avery 121, Blake 123, Casey 124, Drew 132. Mean view length 927 characters; mean full prompt 1,219 characters.

## Baseline diagnostic expectations

- **Independent voting over views.** By P2, an agent that reads its view correctly answers the decoy, so independent plurality voting over correctly read views is expected to score near 0. This follows from the construction, not from a measurement. Arithmetic errors can produce occasional correct answers by chance.
- **Single agent with full evidence.** Expected high; pilot greedy accuracy on the first 50 items was 0.92 for llama3.1:8b and 1.00 for qwen3:14b (`docs/PHASE2_PILOT_REPORT.md`).
- **Communication.** A recovery rate well above independent voting is the intended signal. A 6-item probe with llama3.1:8b gave independent voting over views 0 of 6 and debate over the same views 5 of 6; six items establish nothing, and the confirmatory estimate (hypothesis H2 in `docs/PREREGISTRATION.md`, 200 items) is pending. The figure of 80% or more recovery is a target to test, not a result.
- Strategies are described in `docs/PREREGISTRATION.md`: S2v is independent voting over views; S4 is debate over views.

## Limitations

The task is synthetic and short; models can solve the full-evidence version by addition, so a failure there indicates a model or prompt problem. The partition leaves one pair of criteria with a single holder, which makes the target depend on one agent's message. Names are English given names and not balanced for tokenisation. Item order is fixed by the seed.

## Loading

```python
import json
items = [json.loads(l) for l in open("data/hidden_profile/hidden_profile_v1_seed42_n500.jsonl")]
full, views, gold = items[0]["prompt_full_evidence"], items[0]["views"], items[0]["gold"]
```

## Proposed licence and archiving (author decisions)

CC BY 4.0 for the data, Apache-2.0 for the code, as in the roadmap. Before any upload: author approval, TMLR double-blind rules (a public record can break anonymity), and a dataset-card review. No DOI is claimed.
