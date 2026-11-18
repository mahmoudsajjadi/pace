"""`pace.Session`: framework-neutral call accounting for multi-agent runs (the contract of docs/WORKSHOPS_CERTIFICATION_AND_ADAPTERS_PLAN.md, section 3).

One Session collects one record per model call, with the schema

  session_id, task_id, agent_id, call_id, parent_call_id, provider_response_id, framework_step, declared_round_id, model, provider, started_at, ended_at, elapsed_seconds,
  input_tokens, output_tokens, reasoning_tokens, cache_read_tokens, cache_write_tokens, raw_usage, usage_status, status, error_type, correct

Invariants (each is tested in tests/test_sdk_session.py):
  * missing usage is ``None`` (never 0), and ``usage_status`` says whether the provider reported all, some or none of it;
  * the latency of a call (``elapsed_seconds``) is kept apart from the latency of a task: ``latency_sum_s`` adds the calls (a serial upper bound), ``critical_path_s`` is the
    longest chain through the ``parent_call_id`` graph (overlapping agents are not added), ``wall_clock_s`` is last end minus first start;
  * records are de-duplicated by ``call_id`` and by ``provider_response_id`` (a retry or a double callback counts once);
  * cumulative usage counters (as in some agent SDKs) are not summed: pass each call's own usage in ``raw_usage``.

    with pace.Session("run-1") as s:
        with s.call("q1", "agent_a", model="m", provider="p", declared_round_id=1) as c:
            reply = client.chat(...)
            c.usage(reply.usage)              # provider usage dict, any of the common key spellings
        s.mark("q1", True, agent_id="agent_a", round_id=1)
    s.write_jsonl("pace.jsonl")               # rows that `pace card` reads
"""
from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from typing import Any, Iterator

FIELDS = ("session_id", "task_id", "agent_id", "call_id", "parent_call_id", "provider_response_id", "framework_step", "declared_round_id", "model", "provider", "started_at",
          "ended_at", "elapsed_seconds", "input_tokens", "output_tokens", "reasoning_tokens", "cache_read_tokens", "cache_write_tokens", "raw_usage", "usage_status", "status",
          "error_type", "correct")


def _first(d: dict, *names: str) -> Any:
    for n in names:
        if n in d and d[n] is not None:
            return d[n]
    return None


def normalize_usage(raw: Any) -> dict[str, Any]:
    """Map a provider usage object (OpenAI, Anthropic, Gemini or Ollama style keys) to the five token fields; anything not reported stays None."""
    out = {"input_tokens": None, "output_tokens": None, "reasoning_tokens": None, "cache_read_tokens": None, "cache_write_tokens": None}
    if raw is None:
        return out
    if not isinstance(raw, dict):
        raw = getattr(raw, "__dict__", None) or {}
    comp_details = raw.get("completion_tokens_details") if isinstance(raw.get("completion_tokens_details"), dict) else {}
    prompt_details = raw.get("prompt_tokens_details") if isinstance(raw.get("prompt_tokens_details"), dict) else {}
    out["input_tokens"] = _first(raw, "input_tokens", "prompt_tokens", "promptTokenCount", "prompt_eval_count")
    out["output_tokens"] = _first(raw, "output_tokens", "completion_tokens", "candidatesTokenCount", "eval_count")
    out["reasoning_tokens"] = _first(raw, "reasoning_tokens", "thoughtsTokenCount") if _first(raw, "reasoning_tokens", "thoughtsTokenCount") is not None else comp_details.get("reasoning_tokens")
    out["cache_read_tokens"] = _first(raw, "cache_read_input_tokens", "cache_read_tokens", "cachedContentTokenCount") if _first(raw, "cache_read_input_tokens", "cache_read_tokens", "cachedContentTokenCount") is not None else prompt_details.get("cached_tokens")
    out["cache_write_tokens"] = _first(raw, "cache_creation_input_tokens", "cache_write_tokens")
    return out


def usage_status(tokens: dict[str, Any]) -> str:
    """reported: input and output tokens both present; partial: one of them; missing: neither."""
    have = [tokens.get("input_tokens") is not None, tokens.get("output_tokens") is not None]
    return "reported" if all(have) else ("partial" if any(have) else "missing")


class CallHandle:
    """Filled in by the code inside `with session.call(...) as c:`."""

    def __init__(self, rec: dict[str, Any]):
        self.rec = rec

    def usage(self, raw: Any) -> None:
        self.rec["raw_usage"] = raw if isinstance(raw, (dict, list, str, int, float, type(None))) else repr(raw)
        self.rec.update(normalize_usage(raw))

    def response_id(self, rid: str) -> None:
        self.rec["provider_response_id"] = rid

    def set(self, **fields: Any) -> None:
        self.rec.update(fields)


class Session:
    def __init__(self, session_id: str | None = None, path: str | None = None, clock=time.time):
        self.session_id = session_id or uuid.uuid4().hex[:12]
        self.path = path
        self.calls: list[dict[str, Any]] = []
        self.marks: dict[tuple[str, str | None, int | None], bool] = {}
        self.duplicates = 0
        self._clock = clock
        self._ids: set[str] = set()
        self._rids: set[str] = set()

    def __enter__(self) -> "Session":
        return self

    def __exit__(self, *exc: Any) -> None:
        if self.path:
            self.write_jsonl(self.path)

    # ---------------------------------------------------------------- recording
    def record(self, task_id: str, agent_id: str, **fields: Any) -> dict[str, Any] | None:
        """Add one finished call; returns the stored record, or None when it duplicates an earlier call_id or provider_response_id."""
        rec = {k: None for k in FIELDS}
        rec.update({"session_id": self.session_id, "task_id": str(task_id), "agent_id": str(agent_id), "status": "ok"})
        rec.update({k: v for k, v in fields.items() if k in FIELDS})
        if "raw_usage" in fields and not any(k in fields for k in ("input_tokens", "output_tokens")):
            rec.update(normalize_usage(fields["raw_usage"]))
        rec["call_id"] = str(rec["call_id"] or uuid.uuid4().hex[:12])
        rid = rec["provider_response_id"]
        if rec["call_id"] in self._ids or (rid is not None and rid in self._rids):
            self.duplicates += 1
            return None
        if rec["elapsed_seconds"] is None and rec["started_at"] is not None and rec["ended_at"] is not None:
            rec["elapsed_seconds"] = float(rec["ended_at"]) - float(rec["started_at"])
        rec["usage_status"] = usage_status(rec)
        self._ids.add(rec["call_id"])
        if rid is not None:
            self._rids.add(rid)
        self.calls.append(rec)
        return rec

    @contextmanager
    def call(self, task_id: str, agent_id: str, **fields: Any) -> Iterator[CallHandle]:
        """Time one call. An exception inside the block is recorded as status "error" with its type and then re-raised."""
        rec: dict[str, Any] = dict(fields)
        handle = CallHandle(rec)
        rec["started_at"] = self._clock()
        try:
            yield handle
        except BaseException as e:
            rec["status"], rec["error_type"] = "error", type(e).__name__
            raise
        finally:
            rec["ended_at"] = self._clock()
            self.record(task_id, agent_id, **rec)

    def mark(self, task_id: str, correct: bool, agent_id: str | None = None, round_id: int | None = None) -> None:
        """Score of a task (agent_id and round_id None = the final answer of the task, applied to every call of the task that has no more specific mark)."""
        self.marks[(str(task_id), None if agent_id is None else str(agent_id), None if round_id is None else int(round_id))] = bool(correct)

    # ---------------------------------------------------------------- views
    def _correct_for(self, c: dict[str, Any]) -> bool | None:
        t, a, r = c["task_id"], c["agent_id"], c["declared_round_id"]
        for key in ((t, a, r), (t, a, None), (t, None, r), (t, None, None)):
            if key in self.marks:
                return self.marks[key]
        return c.get("correct")

    def critical_path_s(self, task_id: str | None = None) -> float | None:
        """Longest chain of call durations along parent_call_id links (calls with no parent start a chain); None if no call has a duration."""
        calls = [c for c in self.calls if (task_id is None or c["task_id"] == str(task_id)) and c["elapsed_seconds"] is not None]
        if not calls:
            return None
        by_id = {c["call_id"]: c for c in calls}
        memo: dict[str, float] = {}

        def depth(c, seen=()):
            cid = c["call_id"]
            if cid in memo:
                return memo[cid]
            parent = by_id.get(c["parent_call_id"]) if c["parent_call_id"] not in seen else None
            memo[cid] = float(c["elapsed_seconds"]) + (depth(parent, seen + (cid,)) if parent else 0.0)
            return memo[cid]
        return max(depth(c) for c in calls)

    def summary(self, task_id: str | None = None) -> dict[str, Any]:
        calls = [c for c in self.calls if task_id is None or c["task_id"] == str(task_id)]

        def total(field):
            vals = [c[field] for c in calls if c[field] is not None]
            return (float(sum(vals)) if vals else None), len(calls) - len(vals)
        out: dict[str, Any] = {"session_id": self.session_id, "n_calls": len(calls), "n_duplicates_dropped": self.duplicates, "n_errors": sum(1 for c in calls if c["status"] != "ok")}
        for f in ("input_tokens", "output_tokens", "reasoning_tokens", "cache_read_tokens", "cache_write_tokens"):
            out[f], out[f + "_missing_calls"] = total(f)
        starts = [c["started_at"] for c in calls if c["started_at"] is not None]
        ends = [c["ended_at"] for c in calls if c["ended_at"] is not None]
        sums = [c["elapsed_seconds"] for c in calls if c["elapsed_seconds"] is not None]
        out["latency_sum_s"] = float(sum(sums)) if sums else None
        out["critical_path_s"] = self.critical_path_s(task_id)
        out["wall_clock_s"] = (max(ends) - min(starts)) if starts and ends else None
        return out

    def pace_rows(self) -> list[dict[str, Any]]:
        """Rows for `pace card` / `pace dynamics` (item, agent, round, correct, tokens, latency_s); calls without a score are left out. Missing tokens stay absent, not 0."""
        rows = []
        for c in self.calls:
            ok = self._correct_for(c)
            if ok is None:
                continue
            row = {"item": c["task_id"], "agent": c["agent_id"], "round": c["declared_round_id"] if c["declared_round_id"] is not None else 0, "correct": bool(ok)}
            if c["input_tokens"] is not None:
                row["prompt_tokens"] = c["input_tokens"]
            if c["output_tokens"] is not None:
                row["completion_tokens"] = c["output_tokens"]
            if c["reasoning_tokens"] is not None:
                row["reasoning_tokens"] = c["reasoning_tokens"]
            if c["elapsed_seconds"] is not None:
                row["latency_s"] = c["elapsed_seconds"]
            rows.append(row)
        return rows

    def write_jsonl(self, path: str, calls: bool = False) -> int:
        """Write PACE rows (default) or the raw per-call records."""
        rows = self.calls if calls else self.pace_rows()
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for r in rows:
                fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")
        return len(rows)

    def card(self) -> dict[str, Any]:
        from .card import build_card

        return build_card(self.pace_rows())

    def audit(self, require_usage: bool = False, max_tokens: float | None = None, max_calls: int | None = None) -> list[str]:
        """Problems found in the session (empty list = clean): duplicates, missing usage (if required), token or call ceilings, failed calls."""
        s, problems = self.summary(), []
        if self.duplicates:
            problems.append("%d duplicate call record(s) dropped (same call_id or provider_response_id)" % self.duplicates)
        if require_usage and any(c["usage_status"] != "reported" for c in self.calls):
            problems.append("%d call(s) without reported token usage" % sum(1 for c in self.calls if c["usage_status"] != "reported"))
        if max_calls is not None and s["n_calls"] > max_calls:
            problems.append("%d calls exceed the ceiling of %d" % (s["n_calls"], max_calls))
        if max_tokens is not None:
            if s["input_tokens"] is None or s["output_tokens"] is None:
                problems.append("a token ceiling was set but no usage was reported")
            elif s["input_tokens"] + s["output_tokens"] > max_tokens:
                problems.append("%.0f tokens exceed the ceiling of %.0f" % (s["input_tokens"] + s["output_tokens"], max_tokens))
        if s["n_errors"]:
            problems.append("%d call(s) ended in an error" % s["n_errors"])
        return problems
