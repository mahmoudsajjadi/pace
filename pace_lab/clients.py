"""pace_lab.clients: one logged, cached, resumable call layer for Ollama, Groq and Gemini (standard library only).

    from pace_lab.clients import LLMClient, LLMRequest
    client = LLMClient("outputs/pace_lab/run_001")          # writes calls.jsonl and cache.jsonl there
    res = client.call(LLMRequest(provider="ollama", model="llama3.1:8b", prompt="2+2?", temperature=0.0, seed=1,
                                 max_tokens=64, item_id="i1", strategy="single", round=0, agent_id="a0"))
    res.text, res.status

Design (all of it unit-tested with a fake transport; no network or key is needed to import or test):

* Transport abstraction. Every HTTP exchange goes through `Transport.request`; `UrllibTransport` is the real one, tests inject a fake.
* Providers. Ollama `/api/chat` (+ `/api/tags` for the model digest), Groq's OpenAI-compatible `/chat/completions` (custom User-Agent, key
  from env GROQ_API_KEY), Gemini REST `models/<m>:generateContent` (key from env GEMINI_API_KEY, sent in the `x-goog-api-key` header, never in the URL).
* Retries with exponential backoff on timeouts, connection errors, HTTP 408/429/5xx (Retry-After honoured, capped); other 4xx fail at once.
* A per-provider rate limiter (requests per minute; `None` = unlimited). The default limits are conservative placeholders, not verified free-tier
  numbers: set them from the provider's current documentation before a real run.
* Timeouts: 120 s per attempt by default.
* Log: one JSONL line per attempt in `calls.jsonl` (append-only). Fields: run_id, item_id, strategy, round, agent_id, timestamp, provider, model,
  model_digest (Ollama only, else null), temperature, seed, top_p, max_tokens, prompt_tokens, completion_tokens, reasoning_tokens, reasoning_chars,
  latency_s, text (raw), status (ok | timeout | error | cache_hit), attempt, cached, http_status, finish_reason, error, usage_raw, cache_key.
* Reasoning: `reasoning_tokens` is filled ONLY when the provider reports a count (Groq `completion_tokens_details.reasoning_tokens`, Gemini
  `thoughtsTokenCount`); it is null otherwise and is never inferred. `reasoning_chars` is the length of separable thinking text (Ollama
  `message.thinking`, a `<think>...</think>` block in the content, Groq/gpt-oss `message.reasoning`, Gemini thought parts), null when none is visible.
  `completion_tokens` is whatever the provider reports; `usage_raw` keeps the provider's usage object so the convention can be checked later.
* Cache: `cache.jsonl` (append-only), key = sha256 of the JSON list [provider, model, prompt, temperature, seed, top_p, max_tokens]. A system
  prompt and `extra` options are appended to that list only when non-empty, so the default key matches the specification exactly. Only status-ok
  results are cached; a rerun makes no network call for a cached key (it writes a `cache_hit` log line). The cache is read at start-up, so a
  killed run resumes where it stopped. The model digest is NOT in the key (by specification): if a local model is re-pulled, delete the cache.
* Secrets: keys are read from os.environ at call time (or from a gitignored .env file via `load_dotenv_file`, which the caller must invoke
  explicitly). They are never written to the log, cache, exceptions or reprs; every string that leaves this module is passed through a Redactor
  that removes the exact key values and common key patterns.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import socket
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

DEFAULT_TIMEOUT = 120.0
SECRET_ENV_VARS = ("GROQ_API_KEY", "GEMINI_API_KEY")
DEFAULT_USER_AGENT = "pace-lab/0.1 (+research-harness; python-urllib)"
RETRY_STATUSES = frozenset({408, 429, 500, 502, 503, 504})
# Conservative placeholders (requests per minute). NOT verified provider limits.
DEFAULT_RPM: Dict[str, Optional[float]] = {"ollama": None, "groq": 30.0, "gemini": 10.0}


# ----------------------------------------------------------------------------- errors and redaction
class ClientError(Exception):
    """Base error. Messages are always redacted before the exception is built."""


class MissingKeyError(ClientError):
    """An API key environment variable is not set (the message names the variable, never a value)."""


class TransportError(Exception):
    pass


class TransportTimeout(TransportError):
    pass


_PATTERNS = [
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-~+/=]{8,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"gsk_[A-Za-z0-9]{10,}"),
    re.compile(r"(?i)((?:api[_-]?key|key|token)=)[^&\s\"']+"),
]


class Redactor:
    """Replace known secret values and common key shapes by [REDACTED]. Secrets shorter than 4 characters are ignored."""

    def __init__(self, secrets=()):
        self._secrets: List[str] = []
        for s in secrets:
            self.add(s)

    def add(self, secret: Optional[str]) -> None:
        if not secret or len(secret) < 4:
            return
        for variant in (secret, json.dumps(secret, ensure_ascii=False)[1:-1], json.dumps(secret)[1:-1]):
            if variant and variant not in self._secrets:
                self._secrets.append(variant)
        self._secrets.sort(key=len, reverse=True)

    def __call__(self, text: Any) -> str:
        s = text if isinstance(text, str) else str(text)
        for sec in self._secrets:
            s = s.replace(sec, "[REDACTED]")
        s = _PATTERNS[0].sub(r"\1[REDACTED]", s)
        s = _PATTERNS[1].sub("[REDACTED]", s)
        s = _PATTERNS[2].sub("[REDACTED]", s)
        s = _PATTERNS[3].sub(r"\1[REDACTED]", s)
        return s

    def __repr__(self) -> str:   # never show the secrets
        return "Redactor(n_secrets=%d)" % len(self._secrets)


def load_dotenv_file(path: str, environ: Optional[Dict[str, str]] = None) -> List[str]:
    """Minimal .env reader (KEY=VALUE lines). Sets variables that are not already set; returns the NAMES it set (never the values).
    Opt-in: nothing in this module calls it automatically."""
    env = os.environ if environ is None else environ
    names: List[str] = []
    if not os.path.isfile(path):
        return names
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            if k.startswith("export "):
                k = k[7:].strip()
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            if k and k not in env:
                env[k] = v
                names.append(k)
    return names


# ----------------------------------------------------------------------------- transport
@dataclass
class HttpResponse:
    status: int
    body: str
    headers: Dict[str, str] = field(default_factory=dict)


class Transport:
    def request(self, method: str, url: str, headers: Dict[str, str], body: Optional[bytes], timeout: float) -> HttpResponse:
        raise NotImplementedError


class UrllibTransport(Transport):
    """Real HTTP through urllib. Error messages never include the URL or headers."""

    def request(self, method, url, headers, body, timeout):
        req = urllib.request.Request(url, data=body, headers=dict(headers), method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return HttpResponse(r.status, r.read().decode("utf-8", "replace"), {k.lower(): v for k, v in r.headers.items()})
        except urllib.error.HTTPError as e:
            try:
                text = e.read().decode("utf-8", "replace")
            except Exception:
                text = ""
            return HttpResponse(e.code, text, {k.lower(): v for k, v in (e.headers or {}).items()})
        except (socket.timeout, TimeoutError):
            raise TransportTimeout("timed out after %.0f s" % timeout) from None
        except urllib.error.URLError as e:
            if isinstance(e.reason, (socket.timeout, TimeoutError)):
                raise TransportTimeout("timed out after %.0f s" % timeout) from None
            raise TransportError("connection error: %s" % type(e.reason).__name__) from None
        except OSError as e:
            raise TransportError("connection error: %s" % type(e).__name__) from None


# ----------------------------------------------------------------------------- rate limiter
class RateLimiter:
    """Spaces calls at least 60 / requests_per_minute seconds apart (thread-safe, reservation style). None or 0 = unlimited."""

    def __init__(self, requests_per_minute: Optional[float] = None, clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep):
        self.interval = 60.0 / requests_per_minute if requests_per_minute else 0.0
        self._clock, self._sleep = clock, sleep
        self._next = 0.0
        self._lock = threading.Lock()

    def acquire(self) -> float:
        """Block until a call may start; returns the seconds waited."""
        if not self.interval:
            return 0.0
        with self._lock:
            now = self._clock()
            start = max(now, self._next)
            self._next = start + self.interval
            wait = start - now
        if wait > 0:
            self._sleep(wait)
        return max(wait, 0.0)


# ----------------------------------------------------------------------------- request / result
@dataclass
class LLMRequest:
    provider: str                      # "ollama" | "groq" | "gemini"
    model: str
    prompt: str
    system: Optional[str] = None
    temperature: float = 0.0
    seed: Optional[int] = None
    top_p: float = 1.0
    max_tokens: int = 2048
    extra: Dict[str, Any] = field(default_factory=dict)   # provider options, e.g. {"think": True} (Ollama), {"reasoning_effort": "low"} (Groq)
    # labels, not part of the cache key
    run_id: Optional[str] = None
    item_id: Optional[str] = None
    strategy: Optional[str] = None
    round: Optional[int] = None
    agent_id: Optional[str] = None


@dataclass
class Parsed:
    text: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None
    reasoning_chars: Optional[int] = None
    finish_reason: Optional[str] = None
    usage_raw: Optional[dict] = None


@dataclass
class LLMResult:
    status: str                        # ok | timeout | error
    text: Optional[str]
    record: dict                       # the log line of the final attempt
    cached: bool = False
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def raise_for_status(self) -> None:
        if not self.ok:
            raise ClientError("call failed: status=%s error=%s" % (self.status, self.error))


class ParseError(Exception):
    pass


def cache_key(req: LLMRequest) -> str:
    """sha256 over the JSON list [provider, model, prompt, temperature, seed, top_p, max_tokens] (+ system, extra only when set)."""
    parts: List[Any] = [req.provider, req.model, req.prompt, req.temperature, req.seed, req.top_p, req.max_tokens]
    if req.system:
        parts.append({"system": req.system})
    if req.extra:
        parts.append({"extra": req.extra})
    return hashlib.sha256(json.dumps(parts, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


_THINK_CLOSED = re.compile(r"<think>(.*?)</think>", re.S)


def think_chars(text: str) -> Optional[int]:
    """Characters inside <think> blocks of a response (an unclosed trailing block counts to the end); None when the text has no <think> tag."""
    if not text or "<think>" not in text:
        return None
    total = sum(len(m) for m in _THINK_CLOSED.findall(text))
    rest = _THINK_CLOSED.sub("", text)
    if "<think>" in rest:
        total += len(rest.split("<think>", 1)[1])
    return total


def _int(x: Any) -> Optional[int]:
    return x if isinstance(x, int) and not isinstance(x, bool) else None


# ----------------------------------------------------------------------------- providers
class Provider:
    name = ""
    key_env: Optional[str] = None

    def __init__(self, base_url: str, user_agent: str = DEFAULT_USER_AGENT):
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent

    def build(self, req: LLMRequest, api_key: Optional[str]) -> Tuple[str, str, Dict[str, str], bytes]:
        raise NotImplementedError

    def parse(self, data: dict) -> Parsed:
        raise NotImplementedError

    @staticmethod
    def _messages(req: LLMRequest) -> List[dict]:
        msgs = []
        if req.system:
            msgs.append({"role": "system", "content": req.system})
        msgs.append({"role": "user", "content": req.prompt})
        return msgs


class OllamaProvider(Provider):
    name = "ollama"

    def build(self, req, api_key):
        opts: Dict[str, Any] = {"temperature": req.temperature, "top_p": req.top_p, "num_predict": req.max_tokens}
        if req.seed is not None:
            opts["seed"] = req.seed
        body: Dict[str, Any] = {"model": req.model, "messages": self._messages(req), "stream": False}
        extra = dict(req.extra)
        opts.update(extra.pop("options", {}) or {})
        body.update(extra)                                   # e.g. think, keep_alive
        body["options"] = opts
        return "POST", self.base_url + "/api/chat", {"Content-Type": "application/json", "User-Agent": self.user_agent}, json.dumps(body).encode("utf-8")

    def parse(self, data):
        msg = data.get("message")
        if not isinstance(msg, dict) or "content" not in msg:
            raise ParseError("no message.content in the Ollama response")
        text = msg.get("content") or ""
        thinking = msg.get("thinking")
        rc = len(thinking) if isinstance(thinking, str) else think_chars(text)
        usage = {k: data[k] for k in ("prompt_eval_count", "eval_count", "total_duration", "load_duration", "prompt_eval_duration", "eval_duration") if k in data}
        return Parsed(text=text, prompt_tokens=_int(data.get("prompt_eval_count")), completion_tokens=_int(data.get("eval_count")),
                      reasoning_tokens=None, reasoning_chars=rc, finish_reason=data.get("done_reason"), usage_raw=usage or None)


class GroqProvider(Provider):
    name = "groq"
    key_env = "GROQ_API_KEY"

    def build(self, req, api_key):
        body: Dict[str, Any] = {"model": req.model, "messages": self._messages(req), "temperature": req.temperature, "top_p": req.top_p,
                                "max_completion_tokens": req.max_tokens}
        if req.seed is not None:
            body["seed"] = req.seed
        body.update(req.extra)
        headers = {"Content-Type": "application/json", "Authorization": "Bearer " + str(api_key), "User-Agent": self.user_agent}
        return "POST", self.base_url + "/chat/completions", headers, json.dumps(body).encode("utf-8")

    def parse(self, data):
        try:
            choice = data["choices"][0]
            msg = choice["message"]
        except (KeyError, IndexError, TypeError):
            raise ParseError("no choices[0].message in the Groq response") from None
        text = msg.get("content") or ""
        reasoning = msg.get("reasoning")
        rc = len(reasoning) if isinstance(reasoning, str) else think_chars(text)
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        details = usage.get("completion_tokens_details") if isinstance(usage.get("completion_tokens_details"), dict) else {}
        return Parsed(text=text, prompt_tokens=_int(usage.get("prompt_tokens")), completion_tokens=_int(usage.get("completion_tokens")),
                      reasoning_tokens=_int(details.get("reasoning_tokens")), reasoning_chars=rc, finish_reason=choice.get("finish_reason"),
                      usage_raw=usage or None)


class GeminiProvider(Provider):
    name = "gemini"
    key_env = "GEMINI_API_KEY"

    def build(self, req, api_key):
        gen: Dict[str, Any] = {"temperature": req.temperature, "topP": req.top_p, "maxOutputTokens": req.max_tokens}
        if req.seed is not None:
            gen["seed"] = req.seed
        extra = dict(req.extra)
        gen.update(extra.pop("generationConfig", {}) or {})
        body: Dict[str, Any] = {"contents": [{"role": "user", "parts": [{"text": req.prompt}]}], "generationConfig": gen}
        if req.system:
            body["systemInstruction"] = {"parts": [{"text": req.system}]}
        body.update(extra)
        headers = {"Content-Type": "application/json", "x-goog-api-key": str(api_key), "User-Agent": self.user_agent}
        return "POST", "%s/models/%s:generateContent" % (self.base_url, req.model), headers, json.dumps(body).encode("utf-8")

    def parse(self, data):
        cands = data.get("candidates")
        if not cands:
            fb = data.get("promptFeedback") or {}
            raise ParseError("no candidates (blockReason=%s)" % fb.get("blockReason"))
        cand = cands[0]
        parts = ((cand.get("content") or {}).get("parts")) or []
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict) and not p.get("thought"))
        thought = [p.get("text", "") for p in parts if isinstance(p, dict) and p.get("thought")]
        um = data.get("usageMetadata") if isinstance(data.get("usageMetadata"), dict) else {}
        return Parsed(text=text, prompt_tokens=_int(um.get("promptTokenCount")), completion_tokens=_int(um.get("candidatesTokenCount")),
                      reasoning_tokens=_int(um.get("thoughtsTokenCount")), reasoning_chars=sum(len(t) for t in thought) if thought else None,
                      finish_reason=cand.get("finishReason"), usage_raw=um or None)


# ----------------------------------------------------------------------------- the client
def _utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="milliseconds")


class LLMClient:
    def __init__(self, log_dir: str, run_id: Optional[str] = None, transport: Optional[Transport] = None,
                 rate_limits: Optional[Dict[str, Optional[float]]] = None, max_retries: int = 4, backoff_base: float = 1.0, backoff_max: float = 60.0,
                 timeout: float = DEFAULT_TIMEOUT, ollama_url: str = "http://localhost:11434", groq_url: str = "https://api.groq.com/openai/v1",
                 gemini_url: str = "https://generativelanguage.googleapis.com/v1beta", user_agent: str = DEFAULT_USER_AGENT,
                 environ: Optional[Dict[str, str]] = None, extra_secrets=(), sleep: Callable[[float], None] = time.sleep,
                 monotonic: Callable[[], float] = time.monotonic, wall_clock: Callable[[], float] = time.time,
                 rng: Optional[random.Random] = None, log_name: str = "calls.jsonl", cache_name: str = "cache.jsonl"):
        os.makedirs(log_dir, exist_ok=True)
        self.log_path = os.path.join(log_dir, log_name)
        self.cache_path = os.path.join(log_dir, cache_name)
        self.run_id = run_id or (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6])
        self.transport = transport or UrllibTransport()
        self.max_retries, self.backoff_base, self.backoff_max, self.timeout = max_retries, backoff_base, backoff_max, timeout
        self._environ = os.environ if environ is None else environ
        self._sleep, self._wall = sleep, wall_clock
        self._mono = monotonic
        self._rng = rng or random.Random()
        self.providers: Dict[str, Provider] = {"ollama": OllamaProvider(ollama_url, user_agent), "groq": GroqProvider(groq_url, user_agent),
                                               "gemini": GeminiProvider(gemini_url, user_agent)}
        limits = dict(DEFAULT_RPM)
        limits.update(rate_limits or {})
        self.limiters = {p: RateLimiter(limits.get(p), clock=monotonic, sleep=sleep) for p in self.providers}
        self.redact = Redactor(extra_secrets)
        for var in SECRET_ENV_VARS:
            self.redact.add(self._environ.get(var))
        self._io_lock = threading.Lock()
        self._key_locks: Dict[str, threading.Lock] = {}
        self._digests: Dict[str, Optional[str]] = {}
        self._cache: Dict[str, dict] = {}
        self._load_cache()

    def __repr__(self) -> str:
        return "LLMClient(run_id=%r, log=%r)" % (self.run_id, self.log_path)

    # --- persistence
    def _load_cache(self) -> None:
        if not os.path.isfile(self.cache_path):
            return
        with open(self.cache_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue            # a half-written last line after a crash
                if isinstance(rec, dict) and rec.get("cache_key") and rec.get("status") == "ok":
                    self._cache.setdefault(rec["cache_key"], rec)

    def _append(self, path: str, rec: dict) -> None:
        line = self.redact(json.dumps(rec, ensure_ascii=False))
        with self._io_lock:
            with open(path, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(line + "\n")
                fh.flush()

    @property
    def cache_size(self) -> int:
        return len(self._cache)

    # --- helpers
    def _api_key(self, provider: Provider) -> Optional[str]:
        if not provider.key_env:
            return None
        val = self._environ.get(provider.key_env)
        if not val:
            raise MissingKeyError("environment variable %s is not set" % provider.key_env)
        self.redact.add(val)
        return val

    def model_digest(self, model: str) -> Optional[str]:
        """Digest of a local Ollama model from /api/tags (None when the daemon or the model is not found). Fetched once per model."""
        with self._io_lock:
            if model in self._digests:
                return self._digests[model]
        digest = None
        try:
            r = self.transport.request("GET", self.providers["ollama"].base_url + "/api/tags", {"User-Agent": DEFAULT_USER_AGENT}, None, min(self.timeout, 30.0))
            if r.status == 200:
                models = json.loads(r.body).get("models", [])
                wanted = {model, model if ":" in model else model + ":latest"}
                for m in models:
                    if m.get("name") in wanted or m.get("model") in wanted:
                        digest = m.get("digest")
                        break
        except Exception:
            digest = None
        with self._io_lock:
            self._digests[model] = digest
        return digest

    def _line(self, req: LLMRequest, key: str, attempt: int, status: str, digest: Optional[str], parsed: Optional[Parsed] = None,
              latency: Optional[float] = None, http_status: Optional[int] = None, error: Optional[str] = None, cached: bool = False) -> dict:
        p = parsed
        return {
            "run_id": req.run_id or self.run_id, "item_id": req.item_id, "strategy": req.strategy, "round": req.round, "agent_id": req.agent_id,
            "timestamp": _utc_iso(self._wall()), "provider": req.provider, "model": req.model, "model_digest": digest,
            "temperature": req.temperature, "seed": req.seed, "top_p": req.top_p, "max_tokens": req.max_tokens,
            "prompt_tokens": p.prompt_tokens if p else None, "completion_tokens": p.completion_tokens if p else None,
            "reasoning_tokens": p.reasoning_tokens if p else None, "reasoning_chars": p.reasoning_chars if p else None,
            "latency_s": latency, "text": p.text if p else None, "status": status, "attempt": attempt, "cached": cached,
            "http_status": http_status, "finish_reason": p.finish_reason if p else None, "error": error,
            "usage_raw": p.usage_raw if p else None, "cache_key": key,
        }

    def _delay(self, attempt: int, resp: Optional[HttpResponse]) -> float:
        if resp is not None:
            ra = resp.headers.get("retry-after")
            if ra:
                try:
                    return min(self.backoff_max, max(0.0, float(ra)))
                except ValueError:
                    pass
        return min(self.backoff_max, self.backoff_base * (2 ** (attempt - 1)) * (1.0 + 0.25 * self._rng.random()))

    # --- the call
    def call(self, req: LLMRequest) -> LLMResult:
        if req.provider not in self.providers:
            raise ClientError("unknown provider %r (expected one of %s)" % (req.provider, sorted(self.providers)))
        key = cache_key(req)
        with self._io_lock:
            lock = self._key_locks.setdefault(key, threading.Lock())
        with lock:
            hit = self._cache.get(key)
            if hit is not None:
                p = Parsed(text=hit.get("text") or "", prompt_tokens=hit.get("prompt_tokens"), completion_tokens=hit.get("completion_tokens"),
                           reasoning_tokens=hit.get("reasoning_tokens"), reasoning_chars=hit.get("reasoning_chars"), finish_reason=hit.get("finish_reason"),
                           usage_raw=hit.get("usage_raw"))
                rec = self._line(req, key, 0, "cache_hit", hit.get("model_digest"), p, None, hit.get("http_status"), None, True)
                self._append(self.log_path, rec)
                return LLMResult("ok", p.text, rec, cached=True)
            provider = self.providers[req.provider]
            api_key = self._api_key(provider)
            digest = self.model_digest(req.model) if req.provider == "ollama" else None
            method, url, headers, body = provider.build(req, api_key)
            last: Optional[LLMResult] = None
            for attempt in range(1, self.max_retries + 2):
                self.limiters[req.provider].acquire()
                t0 = self._mono()
                resp: Optional[HttpResponse] = None
                status, err, retry, parsed = "error", None, False, None
                try:
                    resp = self.transport.request(method, url, headers, body, self.timeout)
                except TransportTimeout as e:
                    status, err, retry = "timeout", self.redact(e), True
                except TransportError as e:
                    status, err, retry = "error", self.redact(e), True
                except Exception as e:      # a misbehaving transport must not leak its message (it may contain the URL or headers)
                    status, err, retry = "error", self.redact("%s: %s" % (type(e).__name__, e)), False
                latency = self._mono() - t0
                http_status = resp.status if resp is not None else None
                if resp is not None:
                    if resp.status == 200:
                        try:
                            parsed = provider.parse(json.loads(resp.body))
                            status = "ok"
                        except (ParseError, ValueError, TypeError, AttributeError) as e:
                            status, err = "error", self.redact("unparseable response: %s" % e)
                    else:
                        status, err = "error", self.redact("HTTP %d: %s" % (resp.status, resp.body[:300].replace("\n", " ")))
                        retry = resp.status in RETRY_STATUSES
                rec = self._line(req, key, attempt, status, digest, parsed, round(latency, 6), http_status, err)
                self._append(self.log_path, rec)
                last = LLMResult(status, parsed.text if parsed else None, rec, False, err)
                if status == "ok":
                    self._append(self.cache_path, rec)
                    self._cache[key] = json.loads(self.redact(json.dumps(rec, ensure_ascii=False)))
                    return last
                if not retry or attempt > self.max_retries:
                    return last
                self._sleep(self._delay(attempt, resp))
            return last  # pragma: no cover
