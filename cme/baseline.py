"""cme baseline: a cached, resumable greedy run plus a pool of independent sampled completions.

Every call is appended to a JSONL cache as soon as it finishes, so an interrupted run resumes where it stopped (a record is keyed by
item id, arm and index). Sampled arms use temperature > 0 and a distinct seed per (item, index); the greedy arm uses temperature 0.
Token counts come from the endpoint's usage field. Reasoning tokens are recorded only when the endpoint reports them; otherwise the
field is null and nothing is inferred.

Benchmarks: a JSONL file with one object per line {"id", "question", "answer"}; or the built-in `toy` set (synthetic arithmetic, for
smoke tests only; it says nothing about any model).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.request
from typing import Callable, Dict, Iterable, List, Optional

PROMPT = ("Solve the problem. Think step by step, then finish with a final line of the form 'Answer: <answer>'.\n\nProblem: {q}")


def toy_bench(n: int = 20) -> List[dict]:
    """Synthetic arithmetic items. Not a benchmark: used only to exercise the pipeline."""
    return [{"id": "toy%03d" % i, "question": "What is %d + %d * %d?" % (i + 3, i + 2, 4), "answer": str(i + 3 + (i + 2) * 4)} for i in range(n)]


def load_bench(spec: str, limit: Optional[int] = None) -> List[dict]:
    if spec == "toy":
        items = toy_bench(limit or 20)
    else:
        items = [json.loads(l) for l in open(spec, encoding="utf-8") if l.strip()]
        for it in items:
            if not {"id", "question", "answer"} <= set(it):
                raise ValueError("bench items need id, question and answer")
    return items[:limit] if limit else items


_ANS = re.compile(r"answer\s*[:=]\s*(.+)", re.I)


def extract_answer(text: str) -> str:
    """Last 'Answer: x' line, else the last number or standalone letter A-J, normalised (trimmed, lower-cased, no $ , or trailing period)."""
    m = _ANS.findall(text or "")
    cand = m[-1] if m else ((re.findall(r"-?\d[\d,]*\.?\d*", text or "") or [""])[-1])
    cand = cand.strip().strip("*$ ").rstrip(".").replace(",", "").lower()
    cand = re.sub(r"^\\boxed\{(.*)\}$", r"\1", cand)
    return cand


def norm_gold(a: str) -> str:
    return str(a).strip().rstrip(".").replace(",", "").lower()


class OpenAICompatClient:
    """Minimal client for /v1/chat/completions (Ollama, vLLM, llama.cpp server, OpenAI-compatible hosts). Standard library only."""

    def __init__(self, base_url: str = "http://localhost:11434/v1", api_key: str = "none", timeout: float = 600.0):
        self.base, self.key, self.timeout = base_url.rstrip("/"), api_key, timeout

    def chat(self, model: str, prompt: str, temperature: float, seed: int, max_tokens: int = 2048) -> dict:
        body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": temperature, "seed": seed,
                           "max_tokens": max_tokens, "stream": False}).encode()
        req = urllib.request.Request(self.base + "/chat/completions", data=body,
                                     headers={"Content-Type": "application/json", "Authorization": "Bearer " + self.key})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.loads(r.read())
        lat = time.time() - t0
        msg = data["choices"][0]["message"]
        usage = data.get("usage", {})
        det = usage.get("completion_tokens_details") or {}
        return {"text": msg.get("content") or "", "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
                "reasoning_tokens": det.get("reasoning_tokens"), "latency": lat}


def ollama_digest(model: str, host: str = "http://localhost:11434") -> Optional[str]:
    """Best-effort model digest from Ollama /api/tags; None when unavailable."""
    try:
        with urllib.request.urlopen(host + "/api/tags", timeout=5) as r:
            for m in json.loads(r.read()).get("models", []):
                if m.get("name") == model or m.get("model") == model:
                    return m.get("digest")
    except Exception:
        return None
    return None


def read_cache(path: str) -> Dict[tuple, dict]:
    done: Dict[tuple, dict] = {}
    if os.path.exists(path):
        for l in open(path, encoding="utf-8"):
            if l.strip():
                r = json.loads(l)
                done[(r["item"], r["arm"], r["idx"])] = r
    return done


def sample_seed(base_seed: int, item: str, idx: int) -> int:
    """Distinct, reproducible seed per (item, sample index)."""
    return int(hashlib.sha256(("%d|%s|%d" % (base_seed, item, idx)).encode()).hexdigest()[:8], 16)


def run_baseline(client, model: str, items: Iterable[dict], out_path: str, k: int = 16, temperature: float = 0.7, seed: int = 0,
                 max_tokens: int = 2048, digest: Optional[str] = None, progress: Optional[Callable[[str], None]] = None) -> dict:
    """Run greedy + k sampled completions per item, appending to out_path. Returns counts: new, cached, errors."""
    if temperature <= 0:
        raise ValueError("sampled arms need temperature > 0")
    done = read_cache(out_path)
    new = cached = errors = 0
    with open(out_path, "a", encoding="utf-8") as fh:
        for it in items:
            gold = norm_gold(it["answer"])
            jobs = [("greedy", 0, 0.0)] + [("sample", j, temperature) for j in range(k)]
            for arm, j, temp in jobs:
                if (it["id"], arm, j) in done:
                    cached += 1
                    continue
                s = sample_seed(seed, it["id"], j) if arm == "sample" else seed
                try:
                    r = client.chat(model, PROMPT.format(q=it["question"]), temp, s, max_tokens)
                except Exception as e:  # network or server error: skip and report, do not cache
                    errors += 1
                    if progress:
                        progress("error %s %s %d: %s" % (it["id"], arm, j, e))
                    continue
                ans = extract_answer(r["text"])
                rec = {"item": it["id"], "arm": arm, "idx": j, "seed": s, "temperature": temp, "model": model, "model_digest": digest,
                       "answer": ans, "gold": gold, "correct": ans == gold, "prompt_tokens": r["prompt_tokens"],
                       "completion_tokens": r["completion_tokens"], "reasoning_tokens": r["reasoning_tokens"], "latency": r["latency"]}
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                new += 1
            if progress:
                progress("item %s done (new %d, cached %d, errors %d)" % (it["id"], new, cached, errors))
    return {"new": new, "cached": cached, "errors": errors}


def load_pool(path: str, k: Optional[int] = None):
    """Build a frontier.Pool and the greedy records from a baseline cache. Items lacking k samples are dropped (reported)."""
    from .frontier import Pool
    rows = list(read_cache(path).values())
    by: Dict[str, dict] = {}
    greedy: Dict[str, dict] = {}
    for r in rows:
        if r["arm"] == "greedy":
            greedy[r["item"]] = r
        else:
            d = by.setdefault(r["item"], {"gold": r["gold"], "samples": {}})
            d["samples"][r["idx"]] = r
    need = k or max((len(d["samples"]) for d in by.values()), default=0)
    items = {}
    dropped = 0
    for it, d in by.items():
        ss = [d["samples"][i] for i in sorted(d["samples"])]
        if len(ss) < need or any(s["prompt_tokens"] is None or s["completion_tokens"] is None for s in ss):
            dropped += 1
            continue
        items[it] = {"gold": d["gold"], "answers": [s["answer"] for s in ss[:need]],
                     "tokens": [s["prompt_tokens"] + s["completion_tokens"] for s in ss[:need]]}
    return Pool(items, need), greedy, dropped
