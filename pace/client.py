"""pace.wrap: log the token usage of an existing client without a proxy process (standard library only).

    import pace
    from openai import OpenAI
    client = pace.wrap(OpenAI(), log_path="pace_trace.jsonl")
    with pace.track(item_id="item_042", system="mas", agent="agent_1", round=2):
        response = client.chat.completions.create(model=..., messages=...)

The wrapper forwards every attribute to the wrapped client and intercepts only the calls that return token usage: `chat.completions.create`,
`completions.create` (OpenAI-style clients, sync or async) and a top-level `completion` (a litellm-style module or client). Each successful call
appends one JSON line in the same format as `pace proxy`, so `pace report --logs` and `mae-eval audit` read it. The response is returned unchanged.

Limits (v0.1): streaming calls raise ValueError, because their usage is not known when the call returns and pace never estimates tokens; a response
without a usage block is logged with `usage_missing: true`; prices are never bundled (pass price_in/price_out in USD per million tokens, else cost is null).
"""
from __future__ import annotations

import contextlib
import contextvars
import inspect
import json
import threading
import time
from typing import Any, Dict, Optional

_LABELS: contextvars.ContextVar = contextvars.ContextVar("cme_labels", default={})
_LOCKS: Dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()
_LOGGED = {("chat", "completions", "create"), ("completions", "create"), ("completion",)}


@contextlib.contextmanager
def track(item_id: Optional[str] = None, system: Optional[str] = None, agent: Optional[str] = None, round: Optional[int] = None, **extra):
    """Label every wrapped call made inside the block. Blocks nest; an inner label overrides the outer one. Unset labels keep the outer value."""
    labels = dict(_LABELS.get())
    for key, val in (("item", item_id), ("system", system), ("agent_id", agent), ("round", round)):
        if val is not None:
            labels[key] = val
    labels.update(extra)
    token = _LABELS.set(labels)
    try:
        yield labels
    finally:
        _LABELS.reset(token)


def _get(obj: Any, name: str):
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _record(kwargs: dict, resp: Any, t0: float, t1: float, price_in: Optional[float], price_out: Optional[float]) -> dict:
    usage = _get(resp, "usage")
    pt, ct = _get(usage, "prompt_tokens"), _get(usage, "completion_tokens")
    det = _get(usage, "completion_tokens_details")
    cost = None
    if None not in (price_in, price_out, pt, ct):
        cost = (pt * price_in + ct * price_out) / 1e6
    labels = _LABELS.get()
    choices = _get(resp, "choices") or []
    rec = {"system": labels.get("system", "mas"), "agent_id": labels.get("agent_id", "agent"), "round": int(labels.get("round", 0)),
           "item": str(labels.get("item", "")), "model": _get(resp, "model") or kwargs.get("model"), "prompt_tokens": pt, "completion_tokens": ct,
           "reasoning_tokens": _get(det, "reasoning_tokens"), "n_completions": len(choices) or 1, "start": t0, "end": t1, "latency": t1 - t0, "cost": cost}
    for key, val in labels.items():
        if key not in ("system", "agent_id", "round", "item"):
            rec[key] = val
    if pt is None or ct is None:
        rec["usage_missing"] = True   # logged, never guessed
    return rec


class _Logger:
    def __init__(self, log_path: str, price_in: Optional[float], price_out: Optional[float]):
        self.path, self.price_in, self.price_out = str(log_path), price_in, price_out
        with _LOCKS_GUARD:
            self.lock = _LOCKS.setdefault(self.path, threading.Lock())

    def write(self, kwargs: dict, resp: Any, t0: float, t1: float) -> None:
        line = json.dumps(_record(kwargs, resp, t0, t1, self.price_in, self.price_out), default=str)
        with self.lock, open(self.path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


class _Wrapped:
    """Transparent proxy over a client (or one of its sub-objects); only the usage-returning calls are intercepted."""

    def __init__(self, target: Any, logger: _Logger, path: tuple = ()):
        object.__setattr__(self, "_cme_target", target)
        object.__setattr__(self, "_cme_logger", logger)
        object.__setattr__(self, "_cme_path", path)

    def __getattr__(self, name: str):
        target = object.__getattribute__(self, "_cme_target")
        logger = object.__getattribute__(self, "_cme_logger")
        path = object.__getattribute__(self, "_cme_path") + (name,)
        attr = getattr(target, name)
        if path in _LOGGED and callable(attr):
            return _intercept(attr, logger)
        if callable(attr) or name.startswith("_") or isinstance(attr, (str, int, float, bool, bytes, type(None))):
            return attr
        if any(p[:len(path)] == path for p in _LOGGED):
            return _Wrapped(attr, logger, path)
        return attr

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_cme_target"), name, value)

    def __repr__(self):
        return "pace.wrap(%r)" % (object.__getattribute__(self, "_cme_target"),)

    def __enter__(self):
        target = object.__getattribute__(self, "_cme_target")
        if hasattr(target, "__enter__"):
            target.__enter__()
        return self

    def __exit__(self, *exc):
        target = object.__getattribute__(self, "_cme_target")
        return target.__exit__(*exc) if hasattr(target, "__exit__") else None


def _intercept(fn, logger: _Logger):
    def guard(kwargs: dict) -> None:
        if kwargs.get("stream"):
            raise ValueError("pace.wrap v0.1 does not support streaming calls: usage is not known when the call returns. Use stream=False.")

    if inspect.iscoroutinefunction(fn):
        async def acall(*args, **kwargs):
            guard(kwargs)
            t0 = time.time()
            resp = await fn(*args, **kwargs)
            logger.write(kwargs, resp, t0, time.time())
            return resp
        return acall

    def call(*args, **kwargs):
        guard(kwargs)
        t0 = time.time()
        resp = fn(*args, **kwargs)
        if inspect.isawaitable(resp):   # an async client whose method is not a plain coroutine function
            async def finish():
                out = await resp
                logger.write(kwargs, out, t0, time.time())
                return out
            return finish()
        logger.write(kwargs, resp, t0, time.time())
        return resp
    return call


def wrap(client: Any, log_path: str = "pace_trace.jsonl", price_in: Optional[float] = None, price_out: Optional[float] = None) -> _Wrapped:
    """Return `client` with usage logging on its completion calls. Prices are USD per million tokens; omit them and cost is null."""
    return _Wrapped(client, _Logger(log_path, price_in, price_out))


def log_result(log_path: str, item_id: str, correct: bool, system: Optional[str] = None) -> None:
    """Append the correctness of one item's final answer (the line `pace report` pairs with the logged calls). Call it once per item, after scoring."""
    sysname = system if system is not None else _LABELS.get().get("system", "mas")
    with _LOCKS_GUARD:
        lock = _LOCKS.setdefault(str(log_path), threading.Lock())
    with lock, open(str(log_path), "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"system": sysname, "item": str(item_id), "correct": bool(correct)}) + "\n")
