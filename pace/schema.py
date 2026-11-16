"""Small, dependency-free schemas for portable PACE logs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


def _bool(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "yes", "y", "1", "correct", "right"}:
        return True
    if text in {"false", "no", "n", "0", "incorrect", "wrong"}:
        return False
    raise ValueError("cannot parse boolean value %r" % (value,))


@dataclass
class ItemLog:
    """One scored agent answer at one debate round."""

    item: str
    agent: str
    round: int
    correct: bool
    answer: str | None = None
    prompt_tokens: float | None = None
    completion_tokens: float | None = None

    def __post_init__(self) -> None:
        self.item = str(self.item)
        self.agent = str(self.agent)
        self.round = int(self.round)
        parsed = _bool(self.correct)
        if parsed is None:
            raise ValueError("correct is required")
        self.correct = parsed
        for field in ("prompt_tokens", "completion_tokens"):
            value = getattr(self, field)
            if value is not None and value != "":
                setattr(self, field, float(value))
            else:
                setattr(self, field, None)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        return {key: value for key, value in result.items() if value is not None}


def item_log_from_mapping(row: dict[str, Any]) -> ItemLog:
    """Validate common aliases used by external trace exporters."""
    item = row.get("item", row.get("item_id", row.get("id")))
    agent = row.get("agent", row.get("agent_id", row.get("name", "agent_0")))
    round_no = row.get("round", row.get("round_id", 0))
    correct = row.get("correct", row.get("is_correct"))
    if item is None or correct is None:
        raise ValueError(
            "each record needs item_id/item, agent_id/agent, round, and correct"
        )
    return ItemLog(
        item,
        agent,
        round_no,
        correct,
        row.get("answer"),
        row.get("prompt_tokens"),
        row.get("completion_tokens"),
    )
