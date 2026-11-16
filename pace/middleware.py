"""Runtime accounting middleware, DAG latency, and scaffold decomposition."""

from __future__ import annotations

import functools
import json
from collections.abc import Callable
from typing import Any

from .card import build_card

MODEL_PRICING_USD_PER_1M = {
    name: prices
    for name, prices in {
        "gpt-4o": (5.0, 1.25, 15.0),
        "gpt-4.1": (2.0, 0.5, 8.0),
        "gpt-5": (1.25, 0.125, 10.0),
        "o1": (15.0, 7.5, 60.0),
        "o3": (2.0, 0.5, 8.0),
        "claude-3-5-sonnet": (3.0, 0.3, 15.0),
        "claude-3-7-sonnet": (3.0, 0.3, 15.0),
        "claude-4": (3.0, 0.3, 15.0),
        "gemini-1.5-pro": (1.25, 0.315, 5.0),
        "gemini-2.5-pro": (1.25, 0.125, 10.0),
        "deepseek-r1": (0.55, 0.14, 2.19),
        "deepseek-v3": (0.27, 0.07, 1.1),
        "qwen2.5": (0.4, 0.1, 1.6),
        "llama-3.1-70b": (0.88, 0.0, 0.88),
        "llama-3.3-70b": (0.88, 0.0, 0.88),
        "gpt-4-turbo": (10.0, 0.0, 30.0),
        "claude-3-opus": (15.0, 1.5, 75.0),
        "claude-3-haiku": (0.25, 0.03, 1.25),
        "gemini-1.5-flash": (0.075, 0.01875, 0.3),
        "mistral-large": (2.0, 0.0, 6.0),
        "command-r-plus": (2.5, 0.0, 10.0),
    }.items()
}


def estimate_call_cost(
    model: str,
    prompt_tokens: float,
    completion_tokens: float,
    cached_prompt_tokens: float = 0.0,
    reasoning_tokens: float = 0.0,
    pricing: dict | None = None,
) -> dict:
    """Estimate USD cost while reporting uncached, cached, reasoning, and completion components."""
    table = pricing or MODEL_PRICING_USD_PER_1M
    if (
        model not in table
        or min(prompt_tokens, completion_tokens, cached_prompt_tokens, reasoning_tokens)
        < 0
        or cached_prompt_tokens > prompt_tokens
    ):
        raise ValueError("unknown model or invalid token counts")
    input_price, cached_price, output_price = table[model]
    uncached = prompt_tokens - cached_prompt_tokens
    parts = {
        "uncached_prompt": uncached * input_price / 1e6,
        "cached_prompt": cached_prompt_tokens * cached_price / 1e6,
        "reasoning": reasoning_tokens * output_price / 1e6,
        "completion": completion_tokens * output_price / 1e6,
    }
    return {
        "model": model,
        "input_tokens": prompt_tokens,
        "cached_prompt_tokens": cached_prompt_tokens,
        "reasoning_tokens": reasoning_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": sum(parts.values()),
        "components": parts,
    }


def compute_dag_latency(calls: list[dict]) -> dict:
    if not calls:
        raise ValueError("calls cannot be empty")
    durations = {
        str(call["call_id"]): float(
            call.get(
                "duration_ms",
                float(call.get("end_ms", 0)) - float(call.get("start_ms", 0)),
            )
        )
        for call in calls
    }
    if any(value < 0 for value in durations.values()):
        raise ValueError("durations cannot be negative")
    total = sum(durations.values())
    parents = {
        str(call["call_id"]): [str(dep) for dep in call.get("depends_on", [])]
        for call in calls
    }
    memo = {}

    def longest(node):
        if node in memo:
            return memo[node]
        memo[node] = durations[node] + max(
            (longest(parent) for parent in parents[node]), default=0.0
        )
        return memo[node]

    critical = (
        max((longest(node) for node in durations), default=0.0)
        if any(parents.values())
        else sum(
            max(
                durations[str(call["call_id"])]
                for call in calls
                if call.get("round", 0) == round_no
            )
            for round_no in sorted({call.get("round", 0) for call in calls})
        )
    )
    workers = max(
        sum(1 for call in calls if call.get("round", 0) == round_no)
        for round_no in {call.get("round", 0) for call in calls}
    )
    return {
        "total_sequential_ms": total,
        "critical_path_ms": critical,
        "concurrency_speedup": total / max(critical, 1e-9),
        "max_parallel_workers": workers,
    }


def _word_count(value: Any) -> int:
    if isinstance(value, str):
        return len(value.split())
    if isinstance(value, list):
        return sum(
            _word_count(item.get("content", "") if isinstance(item, dict) else item)
            for item in value
        )
    return 0


def decompose_scaffold_tokens(calls: list[dict]) -> dict:
    if not calls:
        raise ValueError("calls cannot be empty")
    total = sum(
        _word_count(call.get("prompt_text", call.get("messages", "")))
        + float(call.get("completion_tokens", 0))
        for call in calls
    )
    c0 = _word_count(calls[0].get("prompt_text", calls[0].get("messages", "")))
    echoed = sum(
        max(0, _word_count(call.get("prompt_text", call.get("messages", ""))) - c0)
        for call in calls[1:]
    )
    reasoning = sum(
        float(call.get("completion_tokens", call.get("reasoning_tokens", 0)))
        for call in calls
    )
    return {
        "c0": c0,
        "echoed_peer_tokens": echoed,
        "reasoning_tokens": reasoning,
        "total_tokens": total,
        "scaffold_dilution_ratio": 1 - reasoning / total if total else 0.0,
    }


class PaceSession:
    """Collect decorated call records and flush validated JSONL on exit."""

    current: PaceSession | None = None

    def __init__(
        self,
        path: str,
        item: str = "item_0",
        agent: str = "agent_0",
        round_num: int = 1,
    ):
        self.path, self.item, self.agent, self.round_num, self.records = (
            path,
            item,
            agent,
            round_num,
            [],
        )

    def __enter__(self):
        self._previous, PaceSession.current = PaceSession.current, self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            with open(self.path, "w", encoding="utf-8") as handle:
                handle.writelines(json.dumps(row) + "\n" for row in self.records)
        PaceSession.current = self._previous
        return False

    def record(
        self,
        correct: bool,
        answer: str | None = None,
        prompt_tokens: float = 0,
        completion_tokens: float = 0,
    ) -> None:
        self.records.append(
            {
                "item": self.item,
                "agent": self.agent,
                "round": self.round_num,
                "correct": bool(correct),
                "answer": answer,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            }
        )

    def card(self) -> dict:
        return build_card(self.records)


def pace_track(function: Callable) -> Callable:
    """Decorate a function and record its boolean result in the active session."""

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        result = function(*args, **kwargs)
        if PaceSession.current is not None:
            PaceSession.current.record(bool(result), answer=str(result))
        return result

    return wrapper
