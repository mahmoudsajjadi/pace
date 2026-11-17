"""Classify a single-agent baseline into a rung of the baseline ladder (paper Section 3, Figure 1).

Rungs: A greedy single pass; B sampled baseline (k independent samples, no communication, tokens not matched); C a named resource held
equal, or declared single-agent test-time scaling; D a budget sweep or Pareto frontier. The rung describes the baseline a multi-agent
system is compared against, so a configuration that communicates between agents is not a baseline and is rejected.

Five rules, applied in this order (first match wins):
  R1  budget sweep or Pareto frontier (n_budgets >= 3, or pareto true)              -> D
  R2  a named matched resource (thinking tokens, total tokens, cost, latency,
      iterations, generations) with matching declared                              -> C
  R3  extended thinking or search (MCTS, tree search, best-of-n with a verifier)
      without a named matched resource                                             -> C (matching unverified; see `reason`)
  R4  more than one independent sample combined by vote or selection               -> B
  R5  otherwise (one sample, no test-time scaling)                                 -> A

Note on the wording "Rung D: combined multi-agent plus sampling or search architectures": that describes a system under test, not a
baseline, and the paper's Section 3 defines D as a Pareto sweep, so this module follows the paper. Evaluate such combined systems
as the multi-agent side of a contrast against the rung chosen here.

config keys (all optional): n_samples (int), aggregation (e.g. "majority_vote", "best_of_n"), extended_thinking (bool),
thinking_budget (int tokens), search ("mcts", "tree", ...), matched_resource (str), matching_declared (bool, default True when a
resource is named), n_budgets (int), pareto (bool), communication (bool; must be false or absent).
"""
from __future__ import annotations

from typing import Dict, Literal, Tuple

Rung = Literal["A", "B", "C", "D"]
MATCHABLE = {"thinking_tokens", "total_tokens", "tokens", "cost", "latency", "iterations", "generations", "calls", "flops"}
SEARCH = {"mcts", "tree", "tree_search", "beam", "best_first"}


def classify_with_reason(config: Dict) -> Tuple[Rung, str, str]:
    """Return (rung, rule id, reason). Raises ValueError for a communicating configuration or invalid values."""
    if config.get("communication"):
        raise ValueError("a configuration with inter-agent communication is not a single-agent baseline")
    n_samples = int(config.get("n_samples", 1))
    if n_samples < 1:
        raise ValueError("n_samples must be at least 1")
    n_budgets = int(config.get("n_budgets", 0) or 0)
    if config.get("pareto") or n_budgets >= 3:
        return "D", "R1", "budget sweep or Pareto frontier"
    res = str(config.get("matched_resource", "") or "").lower().replace(" ", "_")
    if res:
        if res not in MATCHABLE:
            raise ValueError("unknown matched_resource %r; use one of %s" % (res, sorted(MATCHABLE)))
        if config.get("matching_declared", True):
            return "C", "R2", "resource held equal: %s" % res
    search = str(config.get("search", "") or "").lower()
    aggregation = str(config.get("aggregation", "") or "").lower()
    if config.get("extended_thinking") or config.get("thinking_budget") or search in SEARCH or (aggregation == "best_of_n" and config.get("verifier")):
        return "C", "R3", "extended thinking or search without a named matched resource (matching unverified)"
    if n_samples > 1:
        if aggregation not in ("majority_vote", "vote", "plurality", "best_of_n", "self_consistency", "selection", ""):
            raise ValueError("unknown aggregation %r" % aggregation)
        return "B", "R4", "%d independent samples combined without communication" % n_samples
    return "A", "R5", "single sample, no test-time scaling"


def classify_baseline_rung(config_dict: Dict) -> Rung:
    """Rung (A, B, C or D) of a single-agent baseline configuration."""
    return classify_with_reason(config_dict)[0]
