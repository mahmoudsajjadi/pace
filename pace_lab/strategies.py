"""Deterministic strategy runners over the pace_lab client and grader contracts."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Sequence
from typing import Any

from .clients import LLMClient, LLMRequest
from .graders import Grade, grade_item


def _call(
    client: LLMClient,
    item: dict,
    prompt: str,
    strategy: str,
    round_num: int,
    agent_id: str,
    **extra: Any,
) -> Any:
    request = LLMRequest(
        provider=extra.pop("provider", "ollama"),
        model=extra.pop("model", "local"),
        prompt=prompt,
        temperature=float(extra.pop("temperature", 0.0)),
        seed=extra.pop("seed", 0),
        max_tokens=int(extra.pop("max_tokens", 512)),
        item_id=str(item["id"]),
        strategy=strategy,
        round=round_num,
        agent_id=agent_id,
        extra=extra,
    )
    return client.call(request)


def _grade(item: dict, result: Any) -> Grade:
    return grade_item(item, result.text or "")


def run_s1(client: LLMClient, items: Sequence[dict], **kwargs: Any) -> list[dict]:
    """Run one greedy call per item."""
    return _run_single(client, items, "S1", lambda item: item["prompt"], kwargs)


def _run_single(
    client: LLMClient,
    items: Sequence[dict],
    strategy: str,
    prompt_fn: Callable[[dict], str],
    kwargs: dict,
) -> list[dict]:
    rows = []
    for item in items:
        result = _call(client, item, prompt_fn(item), strategy, 1, "agent_0", **kwargs)
        grade = _grade(item, result)
        rows.append(
            {
                "item": item["id"],
                "strategy": strategy,
                "agent": "agent_0",
                "round": 1,
                "text": result.text,
                "correct": grade.correct,
                "status": result.status,
            }
        )
    return rows


def run_s2(
    client: LLMClient, items: Sequence[dict], k: int = 4, **kwargs: Any
) -> list[dict]:
    """Run a noncommunicating k-sample pool and plurality vote by extracted answer."""
    if k < 1:
        raise ValueError("k must be positive")
    rows = []
    for item in items:
        candidates = []
        for sample in range(k):
            result = _call(
                client,
                item,
                item["prompt"],
                "S2",
                1,
                "sample_%d" % sample,
                seed=sample,
                **kwargs,
            )
            grade = _grade(item, result)
            candidates.append(grade.normalized)
            rows.append(
                {
                    "item": item["id"],
                    "strategy": "S2",
                    "agent": "sample_%d" % sample,
                    "round": 1,
                    "text": result.text,
                    "correct": grade.correct,
                    "answer": grade.normalized,
                    "status": result.status,
                }
            )
        winner = (
            Counter(answer for answer in candidates if answer is not None).most_common(
                1
            )[0][0]
            if any(candidates)
            else None
        )
        rows.append(
            {
                "item": item["id"],
                "strategy": "S2",
                "agent": "vote",
                "round": 2,
                "answer": winner,
                "correct": winner == str(item.get("gold", "")).upper(),
            }
        )
    return rows


def run_s2v(client: LLMClient, items: Sequence[dict], **kwargs: Any) -> list[dict]:
    """Vote over independent split views without exposing other views."""
    return _run_views(client, items, "S2v", 1, kwargs)


def run_s3(client: LLMClient, items: Sequence[dict], **kwargs: Any) -> list[dict]:
    """Run one extended-thinking call per item."""
    kwargs = dict(kwargs)
    kwargs.setdefault("think", True)
    return _run_single(client, items, "S3", lambda item: item["prompt"], kwargs)


def _run_views(
    client: LLMClient, items: Sequence[dict], strategy: str, rounds: int, kwargs: dict
) -> list[dict]:
    rows = []
    for item in items:
        views = item.get("views") or [item["prompt"]]
        for index, view in enumerate(views):
            result = _call(
                client, item, view, strategy, 1, "agent_%d" % index, **kwargs
            )
            grade = _grade(item, result)
            rows.append(
                {
                    "item": item["id"],
                    "strategy": strategy,
                    "agent": "agent_%d" % index,
                    "round": 1,
                    "text": result.text,
                    "correct": grade.correct,
                    "status": result.status,
                }
            )
    return rows


def run_s4(
    client: LLMClient,
    items: Sequence[dict],
    k_agents: int = 3,
    rounds: int = 3,
    **kwargs: Any,
) -> list[dict]:
    """Run homogeneous multi-round debate with explicit transcript context."""
    return _debate(
        client, items, "S4", k_agents, rounds, lambda item, _: item["prompt"], kwargs
    )


def run_s4v(
    client: LLMClient,
    items: Sequence[dict],
    k_agents: int = 3,
    rounds: int = 3,
    **kwargs: Any,
) -> list[dict]:
    """Run split-view debate; each prompt contains only the agent's own view and prior public messages."""
    return _debate(
        client,
        items,
        "S4v",
        k_agents,
        rounds,
        lambda item, agent: (item.get("views") or [item["prompt"]])[agent],
        kwargs,
    )


def _debate(
    client: LLMClient,
    items: Sequence[dict],
    strategy: str,
    k_agents: int,
    rounds: int,
    view_fn: Callable[[dict, int], str],
    kwargs: dict,
) -> list[dict]:
    if k_agents < 1 or rounds < 1:
        raise ValueError("k_agents and rounds must be positive")
    rows = []
    for item in items:
        public = []
        for round_num in range(1, rounds + 1):
            current = []
            for agent in range(k_agents):
                prompt = view_fn(item, agent) + (
                    "\nPublic messages:\n" + "\n".join(public) if public else ""
                )
                result = _call(
                    client,
                    item,
                    prompt,
                    strategy,
                    round_num,
                    "agent_%d" % agent,
                    **kwargs,
                )
                grade = _grade(item, result)
                text = result.text or ""
                current.append(text)
                rows.append(
                    {
                        "item": item["id"],
                        "strategy": strategy,
                        "agent": "agent_%d" % agent,
                        "round": round_num,
                        "text": text,
                        "answer": grade.normalized,
                        "correct": grade.correct,
                        "status": result.status,
                    }
                )
            public = current
    return rows


def run_s5(client: LLMClient, items: Sequence[dict], **kwargs: Any) -> list[dict]:
    """Confidence-weighted debate, represented by a confidence request suffix."""
    kwargs = dict(kwargs)
    kwargs.setdefault("system", "Return an answer and confidence from 0 to 1.")
    return (
        run_s4(client, items, strategy="S5", **kwargs)
        if False
        else _debate(
            client,
            items,
            "S5",
            kwargs.pop("k_agents", 3),
            kwargs.pop("rounds", 3),
            lambda item, _: item["prompt"] + "\nState your confidence.",
            kwargs,
        )
    )


def run_s7(client: LLMClient, items: Sequence[dict], **kwargs: Any) -> list[dict]:
    """Length-matched placebo debate with fixed, noninformative messages."""
    return _debate(
        client,
        items,
        "S7",
        kwargs.pop("k_agents", 3),
        kwargs.pop("rounds", 3),
        lambda item, _: (
            item["prompt"] + "\nContinue independently; do not use peer content."
        ),
        kwargs,
    )


def run_s8(client: LLMClient, items: Sequence[dict], **kwargs: Any) -> list[dict]:
    """Two-layer mixture-of-agents runner: parallel first layer followed by an aggregator call."""
    rows = _run_views(client, items, "S8", 1, kwargs)
    for item in items:
        messages = [row["text"] for row in rows if row["item"] == item["id"]]
        prompt = item["prompt"] + "\nCandidate answers:\n" + "\n".join(messages)
        result = _call(client, item, prompt, "S8", 2, "aggregator", **kwargs)
        grade = _grade(item, result)
        rows.append(
            {
                "item": item["id"],
                "strategy": "S8",
                "agent": "aggregator",
                "round": 2,
                "text": result.text,
                "correct": grade.correct,
                "status": result.status,
            }
        )
    return rows


STRATEGIES = {
    "S1": run_s1,
    "S2": run_s2,
    "S2v": run_s2v,
    "S3": run_s3,
    "S4": run_s4,
    "S4v": run_s4v,
    "S5": run_s5,
    "S7": run_s7,
    "S8": run_s8,
}
