"""ResourceTracker: records model-generation calls and turns them into a ResourceVector.

Token accounting convention (matches vector.py):
  prompt_tokens      all input tokens of a call (includes scaffold_tokens)
  completion_tokens  all output tokens of a call (includes reasoning_tokens)
  scaffold_tokens    the part of prompt_tokens that is system prompt, role declaration, or echoed message history
  reasoning_tokens   the part of completion_tokens that is thinking / scratchpad
Cost is computed from prices YOU register. This library ships no price table: provider prices change and cannot be verified
offline, so a stale default would silently corrupt the r_cost axis.
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable, Dict, Iterator, List, Optional, Tuple

from .vector import ResourceVector


class PricingUnavailable(KeyError):
    """No price registered for (model, tier)."""


@dataclass(frozen=True)
class CallRecord:
    agent_id: str
    prompt_tokens: int
    completion_tokens: int
    reasoning_tokens: int = 0
    scaffold_tokens: int = 0
    tool_calls: int = 0
    n_completions: int = 1
    start: float = 0.0
    end: float = 0.0

    def __post_init__(self) -> None:
        if min(self.prompt_tokens, self.completion_tokens, self.reasoning_tokens, self.scaffold_tokens, self.tool_calls) < 0:
            raise ValueError("token and tool counts must be >= 0")
        if self.reasoning_tokens > self.completion_tokens:
            raise ValueError("reasoning_tokens cannot exceed completion_tokens")
        if self.scaffold_tokens > self.prompt_tokens:
            raise ValueError("scaffold_tokens cannot exceed prompt_tokens")
        if self.n_completions < 0:
            raise ValueError("n_completions must be >= 0 (0 for pure tool calls)")
        if self.end < self.start:
            raise ValueError("end before start")


class Session:
    """Holds the calls recorded inside one tracker.trace() block."""

    def __init__(self, tracker: "ResourceTracker", clock: Callable[[], float]):
        self._tracker = tracker
        self._clock = clock
        self.calls: List[CallRecord] = []

    def record_call(self, agent_id: str, prompt_tokens: int, completion_tokens: int, *, reasoning_tokens: int = 0,
                    scaffold_tokens: int = 0, tool_calls: int = 0, n_completions: int = 1,
                    start: Optional[float] = None, end: Optional[float] = None) -> CallRecord:
        """Record one generation call. Pass explicit start/end (seconds) to describe concurrent calls; otherwise
        both default to the tracker clock (zero duration)."""
        now = self._clock()
        rec = CallRecord(agent_id, int(prompt_tokens), int(completion_tokens), int(reasoning_tokens), int(scaffold_tokens),
                         int(tool_calls), int(n_completions), now if start is None else float(start), now if end is None else float(end))
        self.calls.append(rec)
        return rec

    def record_stream(self, agent_id: str, prompt_tokens: int, chunks, *, reasoning_tokens: int = 0, scaffold_tokens: int = 0,
                      tool_calls: int = 0, start: Optional[float] = None, chunk_times=None) -> CallRecord:
        """Record one streamed completion. `chunks` is an iterable of token counts per streamed chunk; the completion token
        count is their sum. `chunk_times` (optional, same length) gives each chunk's arrival time; the call ends at the last one."""
        chunks = [int(c) for c in chunks]
        if not chunks:
            raise ValueError("a streamed completion needs at least one chunk")
        if any(c < 0 for c in chunks):
            raise ValueError("chunk token counts must be >= 0")
        t0 = self._clock() if start is None else float(start)
        end = t0
        if chunk_times is not None:
            chunk_times = [float(t) for t in chunk_times]
            if len(chunk_times) != len(chunks):
                raise ValueError("chunk_times must match chunks")
            end = max(chunk_times)
        return self.record_call(agent_id, prompt_tokens, sum(chunks), reasoning_tokens=reasoning_tokens, scaffold_tokens=scaffold_tokens,
                                tool_calls=tool_calls, start=t0, end=end)

    def record_tool_call(self, agent_id: str, *, attempts: int = 1, start: Optional[float] = None, end: Optional[float] = None) -> CallRecord:
        """Record a tool invocation. Every attempt, including retries, counts toward r_sys; the interval from `start` to `end`
        (spanning all attempts and back-off waits) counts toward wall-clock latency. No model tokens or completions are added."""
        if attempts < 1:
            raise ValueError("attempts must be >= 1")
        return self.record_call(agent_id, 0, 0, tool_calls=attempts, n_completions=0, start=start, end=end)

    # ---- aggregates ----
    @property
    def serial_latency(self) -> float:
        return sum(c.end - c.start for c in self.calls)

    @property
    def makespan(self) -> float:
        """Wall-clock time from the first call start to the last call end (concurrent calls overlap)."""
        if not self.calls:
            return 0.0
        return max(c.end for c in self.calls) - min(c.start for c in self.calls)

    def get_resource_vector(self, allow_missing_pricing: bool = False) -> ResourceVector:
        if not self.calls:
            raise ValueError("no calls recorded")
        prompt = sum(c.prompt_tokens for c in self.calls)
        completion = sum(c.completion_tokens for c in self.calls)
        try:
            cost: Optional[float] = self._tracker.price(prompt, completion)
        except PricingUnavailable:
            if not allow_missing_pricing:
                raise
            cost = None
        vec = ResourceVector(
            r_reason=float(sum(c.reasoning_tokens for c in self.calls)),
            r_token=float(prompt + completion),
            r_cost=cost,
            r_lat=self.makespan,
            r_sample=int(sum(c.n_completions for c in self.calls)),
            r_sys=int(sum(c.tool_calls for c in self.calls)),
            r_scaffold=float(sum(c.scaffold_tokens for c in self.calls)),
        )
        return vec.validate(strict=cost is not None)

    def scaffold_by_agent(self) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for c in self.calls:
            out[c.agent_id] = out.get(c.agent_id, 0.0) + c.scaffold_tokens
        return out


class ResourceTracker:
    """Usage: tracker = ResourceTracker(model, pricing_tier); tracker.register_pricing(...); with tracker.trace() as s: ..."""

    _PRICES: Dict[Tuple[str, str], Tuple[float, float]] = {}

    def __init__(self, model: str, pricing_tier: str = "standard", clock: Callable[[], float] = time.monotonic):
        self.model = model
        self.pricing_tier = pricing_tier
        self._clock = clock
        self._prices: Dict[Tuple[str, str], Tuple[float, float]] = {}

    def register_pricing(self, input_usd_per_mtok: float, output_usd_per_mtok: float,
                         model: Optional[str] = None, tier: Optional[str] = None) -> None:
        if input_usd_per_mtok < 0 or output_usd_per_mtok < 0:
            raise ValueError("prices must be >= 0")
        self._prices[(model or self.model, tier or self.pricing_tier)] = (float(input_usd_per_mtok), float(output_usd_per_mtok))

    def price(self, prompt_tokens: int, completion_tokens: int) -> float:
        key = (self.model, self.pricing_tier)
        if key not in self._prices:
            raise PricingUnavailable("no price registered for %s/%s; call register_pricing()" % key)
        pin, pout = self._prices[key]
        return (prompt_tokens * pin + completion_tokens * pout) / 1e6

    @contextmanager
    def trace(self) -> Iterator[Session]:
        yield Session(self, self._clock)
