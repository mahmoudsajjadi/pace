"""Controlled-experiment harness: strategies 1-9 on the same items with the same model (Phase 2).

Strategy numbers follow docs/PHASED_EXPERIMENT_AND_TOOL_ROADMAP.md section 2:
  1 greedy, one call                          2 pool of k=16 independent samples (self-consistency curve for k = 1..16)
  3 one call with more thinking               4 vanilla debate (5 copies of one model, 3 rounds; round 1 = pool samples 0-4)
  5 debate with confidence-weighted aggregation   6 debate among different models (+ 6v: vote by the same mix, no communication)
  7 placebo debate (peer messages replaced by unrelated text of matched length)    8 mixture-of-agents aggregator (2 layers)
  9 verifier (code tasks): agents receive unit-test feedback; the independent arm gets the same verifier (best of the pool)
Round-1 answers of strategies 4, 5, 7 and 8 are the first five pool samples, so debate and voting differ only by the messages; the
tokens of reused calls are still charged to the strategy that uses them. Every call is cached in calls.jsonl (resumable), every
strategy outcome is written to results.jsonl. Nothing here is a result: results exist only for runs whose files exist.
Limitation: Ollama's prompt_eval_count can exclude prompt tokens served from its KV cache, so prompt tokens may be undercounted on
repeated prefixes; completion tokens and wall time are exact for the call.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from typing import Dict, List, Optional

from . import tasks as T

THINK_MODELS = ("qwen3:", "deepseek-r1:", "qwen3.5:")   # Ollama 'think' flag is passed only to these
SOLVE = "{q}\n\nThink step by step. Finish with two final lines: 'Answer: <answer>' and 'Confidence: <0-100>'."
SOLVE_CODE = "{q}\n\nAfter the code block add a final line 'Confidence: <0-100>'."
EXTENDED = ("{q}\n\nReason for much longer than usual: work the problem out fully, then re-check your work independently twice before answering. "
            "Finish with two final lines: 'Answer: <answer>' and 'Confidence: <0-100>'.")
DEBATE = ("{q}\n\nYour previous response:\n{own}\n\nOther agents responded:\n{peers}\n\nUse their reasoning as additional information, but verify it yourself. "
          "Give your updated solution. Finish with two final lines: 'Answer: <answer>' and 'Confidence: <0-100>'.")
MOA = ("{q}\n\nCandidate responses from other solvers:\n{cands}\n\nSynthesize the best final solution, correcting errors you find. "
       "Finish with two final lines: 'Answer: <answer>' and 'Confidence: <0-100>'.")
FEEDBACK = "{q}\n\nYour previous code:\n```python\n{code}\n```\nIt was run against the unit tests and {status}.\nGive a corrected version in a ```python block, then a final line 'Confidence: <0-100>'."
TAIL = 800


class OllamaClient:
    """Ollama native /api/chat client: real token counts (prompt_eval_count, eval_count) and wall time per call."""

    def __init__(self, host: str = "http://localhost:11434", num_ctx: int = 8192, timeout: float = 1800.0):
        self.host, self.num_ctx, self.timeout = host.rstrip("/"), num_ctx, timeout

    def chat(self, model: str, prompt: str, temperature: float, seed: int, max_tokens: int = 2048, think: Optional[bool] = None) -> dict:
        body = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False,
                "options": {"temperature": temperature, "seed": seed, "num_predict": max_tokens, "num_ctx": self.num_ctx}}
        if think is not None and model.startswith(THINK_MODELS):
            body["think"] = think
        req = urllib.request.Request(self.host + "/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            d = json.loads(r.read())
        m = d.get("message", {})
        return {"text": m.get("content") or "", "thinking_chars": len(m.get("thinking") or ""), "prompt_tokens": d.get("prompt_eval_count"),
                "completion_tokens": d.get("eval_count"), "latency": time.time() - t0, "done_reason": d.get("done_reason")}


class Store:
    """Append-only JSONL cache of calls keyed by a string; reloaded on start so interrupted runs resume."""

    def __init__(self, path: str):
        self.path, self.d = path, {}
        self._lock = threading.Lock()
        if os.path.exists(path):
            for l in open(path, encoding="utf-8"):
                if l.strip():
                    r = json.loads(l)
                    self.d[r["key"]] = r

    def put(self, rec: dict) -> None:
        with self._lock:
            self.d[rec["key"]] = rec
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")


class Ctx:
    def __init__(self, client, store: Store, model: str, models: Optional[List[str]] = None, k: int = 16, agents: int = 5, rounds: int = 3,
                 seed: int = 0, temperature: float = 0.7, max_tokens: int = 2048, think_tokens: int = 8192,
                 price_in: Optional[float] = None, price_out: Optional[float] = None, retries: int = 3, think_default: bool = False):
        self.client, self.store, self.model = client, store, model
        self.models = models or [model]
        self.k, self.agents, self.rounds, self.seed, self.temperature = k, agents, rounds, seed, temperature
        self.max_tokens, self.think_tokens = max_tokens, think_tokens
        self.price_in, self.price_out, self.retries = price_in, price_out, retries
        self.think_default = think_default   # value of the Ollama `think` flag for ordinary calls (True lets reasoning models report thinking separately)
        self.used: List[dict] = []
        self._digests: Dict[str, Optional[str]] = {}

    def call(self, key: str, model: str, prompt: str, temperature: float, max_tokens: Optional[int] = None, think: Optional[bool] = None,
             comm_chars: int = 0) -> dict:
        rec = self.store.d.get(key)
        if rec is None:
            seed = int(hashlib.sha256((str(self.seed) + key).encode()).hexdigest()[:8], 16) if temperature > 0 else self.seed
            r = None
            for attempt in range(self.retries + 1):
                try:
                    r = self.client.chat(model, prompt, temperature, seed, max_tokens or self.max_tokens, think)
                    break
                except (urllib.error.URLError, TimeoutError, ConnectionError):   # transient server errors only
                    if attempt == self.retries:
                        raise
                    time.sleep(5 * (attempt + 1))
            cost = None
            if None not in (self.price_in, self.price_out, r.get("prompt_tokens"), r.get("completion_tokens")):
                cost = (r["prompt_tokens"] * self.price_in + r["completion_tokens"] * self.price_out) / 1e6   # local calls: prices 0.0
            if model not in self._digests:
                from .baseline import ollama_digest
                self._digests[model] = ollama_digest(model, getattr(self.client, "host", "http://localhost:11434")) if hasattr(self.client, "host") else None
            rec = {"key": key, "model": model, "model_digest": self._digests[model], "temperature": temperature, "seed": seed, "think": think,
                   "cost_usd": cost, "reasoning_tokens": None, "prompt_chars": len(prompt), "comm_chars": comm_chars, **r}
            self.store.put(rec)
        self.used.append(rec)
        return rec

    def begin(self):
        self.used = []

    def fork(self) -> "Ctx":
        """A worker context sharing the client and the call store, with its own `used` list (thread safe)."""
        c = Ctx(self.client, self.store, self.model, self.models, self.k, self.agents, self.rounds, self.seed, self.temperature, self.max_tokens,
                self.think_tokens, self.price_in, self.price_out, self.retries, self.think_default)
        c._digests = self._digests
        return c


def _solve_prompt(item, q=None):
    return (SOLVE_CODE if item["kind"] == "code" else SOLVE).format(q=q or item["prompt"])


def ans_of(item, rec) -> str:
    """Normalised answer of a call (for code: pass/fail marker computed by running the tests)."""
    if item["kind"] == "code":
        return "pass" if T.score(item, rec["text"]) else "fail"
    return T.normalize_answer(item, T.parse_answer(rec["text"]))


def vote(answers: List[str], gold_answer_fn, weights: Optional[List[float]] = None):
    """Plurality (or weighted) vote. Returns (leaders, credit) where credit is 1/m if the gold is among m tied leaders."""
    c: Counter = Counter()
    for a, w in zip(answers, weights or [1.0] * len(answers)):
        if a != "":
            c[a] += w
    if not c:
        return [], 0.0
    top = max(c.values())
    leaders = sorted(a for a, v in c.items() if abs(v - top) < 1e-12)
    return leaders, (1.0 / len(leaders)) if any(gold_answer_fn(a) for a in leaders) else 0.0


def _is_gold(item):
    if item["kind"] == "text":
        gs = {T._norm_text(x) for x in item["gold"]}
        return lambda a: a in gs
    if item["kind"] == "num":
        return lambda a: a == T._norm_num(item["gold"])
    if item["kind"] == "name":
        return lambda a: a == str(item["gold"]).lower()
    return lambda a: a == str(item["gold"]).upper()


def _tail(text: str, n: int = TAIL) -> str:
    t = (text or "").strip()
    return t[-n:] if len(t) > n else t


def pool_rec(ctx: Ctx, item: dict, idx: int, model: Optional[str] = None) -> dict:
    m = model or ctx.model
    return ctx.call("pool|%s|%s|%d" % (m, item["id"], idx), m, _solve_prompt(item), ctx.temperature, think=ctx.think_default)


def round1(ctx: Ctx, item: dict, n: int) -> List[dict]:
    """Round-1 responses: pool samples 0..n-1, or one call per agent view when evidence is split."""
    if item.get("views"):
        return [ctx.call("r1v|%s|%s|%d" % (ctx.model, item["id"], i), ctx.model, _solve_prompt(item, item["views"][i % len(item["views"])]), ctx.temperature, think=ctx.think_default)
                for i in range(n)]
    return [pool_rec(ctx, item, i) for i in range(n)]


def _result(ctx, strategy, item, credit, final, extra=None):
    toks = lambda f: sum((r.get(f) or 0) for r in ctx.used)
    out = {"strategy": strategy, "model": ctx.model if len(ctx.models) == 1 else "+".join(ctx.models), "item": item["id"], "task": item["task"],
           "correct": credit, "final": final, "calls": len(ctx.used), "prompt_tokens": toks("prompt_tokens"), "completion_tokens": toks("completion_tokens"),
           "latency_sum": toks("latency"), "keys": [r["key"] for r in ctx.used]}
    if extra:
        out.update(extra)
    return out


# ------------------------------------------------------------------------------------ strategies
def s1_greedy(ctx, item):
    r = ctx.call("greedy|%s|%s" % (ctx.model, item["id"]), ctx.model, _solve_prompt(item), 0.0, think=ctx.think_default)
    return _result(ctx, "S1", item, float(T.score(item, r["text"])), ans_of(item, r))


def s2_pool(ctx, item):
    recs = [pool_rec(ctx, item, i) for i in range(ctx.k)]
    if item["kind"] == "code":
        passes = [ans_of(item, r) == "pass" for r in recs]
        return _result(ctx, "S2", item, sum(passes) / len(passes), "pass@1 mean", {"pass_any": any(passes)})
    leaders, cr = vote([ans_of(item, r) for r in recs], _is_gold(item))
    res = _result(ctx, "S2", item, cr, "|".join(leaders))
    if item.get("views"):  # split evidence: independent agents each see one view, no communication, then vote
        ctx.begin()
        v = round1(ctx, item, ctx.agents)
        lv, crv = vote([ans_of(item, r) for r in v], _is_gold(item))
        return [res, _result(ctx, "S2v", item, crv, "|".join(lv))]
    return res


def s3_think(ctx, item):
    cap = ctx.model.startswith(THINK_MODELS)
    prompt = _solve_prompt(item) if cap else EXTENDED.format(q=item["prompt"]) if item["kind"] != "code" else _solve_prompt(item)
    r = ctx.call("think|%s|%s" % (ctx.model, item["id"]), ctx.model, prompt, 0.0, ctx.think_tokens if cap else 4096, think=True if cap else None)
    return _result(ctx, "S3", item, float(T.score(item, r["text"])), ans_of(item, r), {"mode": "think-flag" if cap else "prompt-extended", "thinking_chars": r.get("thinking_chars")})


def _peers(ctx, texts, j, show_conf: bool, placebo_texts=None, transform=None):
    lines = []
    for q, t in enumerate(texts):
        if q == j:
            continue
        body = _tail(t)
        if transform is not None:
            body = transform(body, q, j)
        if placebo_texts is not None:
            p = placebo_texts[q % len(placebo_texts)]
            body = (p * (len(body) // max(1, len(p)) + 1))[: len(body)]
        conf = T.parse_confidence(t)
        lines.append("Agent %d%s: %s" % (q + 1, (" (confidence %.0f%%)" % (100 * conf)) if (show_conf and conf is not None) else "", body))
    return "\n\n".join(lines)


def _debate(ctx, item, strategy, models, r1_recs, show_conf, weighted, placebo_pool=None, peer_transform=None):
    cur = list(r1_recs)
    rounds_ans = [[ans_of(item, r) for r in cur]]
    rounds_tok = [[[r.get("prompt_tokens"), r.get("completion_tokens")] for r in cur]]
    for rd in range(2, ctx.rounds + 1):
        texts = [r["text"] for r in cur]
        nxt = []
        for j in range(len(cur)):
            peers = _peers(ctx, texts, j, show_conf, placebo_pool, peer_transform)
            # split evidence: an agent sees only its own view in every round (before 2026-11-12 the later rounds showed the full-evidence prompt to every agent; see docs/PREREGISTRATION_ADDENDUM_2.md)
            q = item["views"][j % len(item["views"])] if item.get("views") else item["prompt"]
            prompt = DEBATE.format(q=q, own=_tail(texts[j]), peers=peers)
            nxt.append(ctx.call("%s|%s|%s|r%d|a%d" % (strategy, "+".join(models), item["id"], rd, j), models[j], prompt, ctx.temperature, think=ctx.think_default,
                                comm_chars=len(peers)))
        cur = nxt
        rounds_ans.append([ans_of(item, r) for r in cur])
        rounds_tok.append([[r.get("prompt_tokens"), r.get("completion_tokens")] for r in cur])
    answers = [ans_of(item, r) for r in cur]
    w = [T.parse_confidence(r["text"]) or 0.5 for r in cur] if weighted else None
    leaders, cr = vote(answers, _is_gold(item), w)
    changed = sum(1 for a, b in zip([ans_of(item, r) for r in r1_recs], answers) if a != b)
    return leaders, cr, {"answers_changed": changed, "round_answers": rounds_ans, "round_tokens": rounds_tok}


def s4_debate(ctx, item):
    # Items with split evidence run as S4v (own keys, own label) so that results of the earlier implementation, which leaked the full evidence in rounds 2 and later, are never reused.
    name = "S4v" if item.get("views") else "S4"
    leaders, cr, ex = _debate(ctx, item, name, [ctx.model] * ctx.agents, round1(ctx, item, ctx.agents), False, False)
    return _result(ctx, name, item, cr, "|".join(leaders), ex)


def s5_conf_debate(ctx, item):
    leaders, cr, ex = _debate(ctx, item, "S5", [ctx.model] * ctx.agents, round1(ctx, item, ctx.agents), True, True)
    return _result(ctx, "S5", item, cr, "|".join(leaders), ex)


def s6_hetero(ctx, item):
    """Debate among different models, and (S6v) vote by the same mix with no communication. Returns two results."""
    ms = [ctx.models[i % len(ctx.models)] for i in range(ctx.agents)]
    r1 = [pool_rec(ctx, item, i // len(ctx.models), ms[i]) for i in range(ctx.agents)]
    lv, crv = vote([ans_of(item, r) for r in r1], _is_gold(item))
    vote_res = _result(ctx, "S6v", item, crv, "|".join(lv))
    leaders, cr, ex = _debate(ctx, item, "S6", ms, r1, False, False)
    deb = _result(ctx, "S6", item, cr, "|".join(leaders), ex)
    return [vote_res, deb]


def s7_placebo(ctx, item, others: List[dict]):
    r1 = round1(ctx, item, ctx.agents)
    n_used = len(ctx.used)
    foreign = [pool_rec(ctx, others[i % len(others)], i)["text"] for i in range(ctx.agents)]
    del ctx.used[n_used:]   # the borrowed text is input material for the control, not compute spent on this item
    leaders, cr, ex = _debate(ctx, item, "S7", [ctx.model] * ctx.agents, r1, False, False, placebo_pool=[_tail(t) for t in foreign])
    return _result(ctx, "S7", item, cr, "|".join(leaders), ex)


def s8_moa(ctx, item):
    props = round1(ctx, item, ctx.agents)
    cands = "\n\n".join("[%d] %s" % (i + 1, _tail(r["text"])) for i, r in enumerate(props))
    l1 = [ctx.call("S8|L1|%s|%s|%d" % (ctx.model, item["id"], i), ctx.model, MOA.format(q=item["prompt"], cands=cands), ctx.temperature, think=ctx.think_default) for i in range(ctx.agents)]
    cands2 = "\n\n".join("[%d] %s" % (i + 1, _tail(r["text"])) for i, r in enumerate(l1))
    fin = ctx.call("S8|L2|%s|%s" % (ctx.model, item["id"]), ctx.model, MOA.format(q=item["prompt"], cands=cands2), 0.0, think=ctx.think_default)
    return _result(ctx, "S8", item, float(T.score(item, fin["text"])), ans_of(item, fin))


def s9_verifier(ctx, item):
    """Code only. Feedback arm: agent revises with unit-test results (up to rounds-1 revisions). Independent arm: best of the pool with the same verifier."""
    if item["kind"] != "code":
        raise ValueError("strategy 9 needs a code task")
    ok = lambda rec: T.score(item, rec["text"])
    pool = [pool_rec(ctx, item, i) for i in range(ctx.agents)]
    ind = any(ok(r) for r in pool)
    ind_res = _result(ctx, "S9i", item, float(ind), "verified best-of-%d" % ctx.agents)
    ctx.begin()
    cur, solved = pool[0], ok(pool[0])
    for rd in range(2, ctx.rounds + 1):
        if solved:
            break
        prompt = FEEDBACK.format(q=item["prompt"], code=T.extract_code(cur["text"]), status="failed" if not solved else "passed")
        cur = ctx.call("S9|%s|%s|r%d" % (ctx.model, item["id"], rd), ctx.model, prompt, ctx.temperature, think=ctx.think_default)
        solved = ok(cur)
    ctx.used = [pool[0]] + [r for r in ctx.used if r is not pool[0]]
    fb_res = _result(ctx, "S9", item, float(solved), "feedback loop")
    return [ind_res, fb_res]


def s10_views_vote(ctx, item):
    """Independent agents on split evidence, plurality vote (the S2v arm of strategy 2 without the 16-sample pool)."""
    if not item.get("views"):
        raise ValueError("strategy 10 needs a split-evidence task")
    v = round1(ctx, item, ctx.agents)
    lv, crv = vote([ans_of(item, r) for r in v], _is_gold(item))
    return _result(ctx, "S2v", item, crv, "|".join(lv))


def load_items(task, n, stratify=False, evidence="split"):
    """Task items; evidence='shared' removes the per-agent views of split-evidence items, so every agent sees all evidence (the redundant-evidence arm of the 2x2 design)."""
    items = T.load_task(task, n, stratify=stratify)
    if evidence == "shared":
        items = [{k: v for k, v in it.items() if k != "views"} for it in items]
    elif evidence != "split":
        raise ValueError("evidence must be 'split' or 'shared'")
    return items


STRATS = {1: s1_greedy, 2: s2_pool, 3: s3_think, 4: s4_debate, 5: s5_conf_debate, 6: s6_hetero, 7: s7_placebo, 8: s8_moa, 9: s9_verifier, 10: s10_views_vote}


def run(ctx: Ctx, items: List[dict], strategies: List[int], out_dir: str, progress=print, workers: int = 1) -> dict:
    """Run strategies over items. Strategy 2 always runs first (the pool feeds debate round 1 and the placebo text). With workers > 1,
    items of one strategy run concurrently; item failures are logged to errors.jsonl and the item is skipped, never filled in."""
    from concurrent.futures import ThreadPoolExecutor
    os.makedirs(out_dir, exist_ok=True)
    rpath, epath = os.path.join(out_dir, "results.jsonl"), os.path.join(out_dir, "errors.jsonl")
    order = sorted(set(strategies), key=lambda x: (x != 2, strategies.index(x)))
    if 7 in order and 2 not in order:
        order.insert(0, 2)
    done = set()
    if os.path.exists(rpath):
        for l in open(rpath, encoding="utf-8"):
            if l.strip():
                r = json.loads(l)
                done.add((r["strategy"], r["item"]))
    lock = threading.Lock()
    counts = {"new": 0, "errors": 0, "done_items": 0}
    t0 = time.time()
    label = {1: "S1", 2: "S2", 3: "S3", 4: "S4", 5: "S5", 6: "S6", 7: "S7", 8: "S8", 9: "S9", 10: "S2v", 11: "S4v", 12: "S12", 13: "S13"}

    def work(args):
        s, item = args
        lab = "S4v" if (s == 4 and item.get("views")) else label[s]
        if (lab, item["id"]) in done:
            return
        c = ctx.fork()
        c.begin()
        try:
            res = STRATS[s](c, item, [x for x in items if x is not item]) if s == 7 else STRATS[s](c, item)
        except Exception as e:   # record and continue: no result is invented for a failed item
            with lock:
                counts["errors"] += 1
                with open(epath, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"strategy": label[s], "item": item["id"], "error": repr(e)[:300]}) + "\n")
            return
        with lock:
            for r in (res if isinstance(res, list) else [res]):
                with open(rpath, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(r) + "\n")
                counts["new"] += 1
            counts["done_items"] += 1
            if progress and counts["done_items"] % 10 == 0:
                progress("%s: %d items finished, %.0fs, errors %d" % (label[s], counts["done_items"], time.time() - t0, counts["errors"]))

    for s in order:
        if s == 9 and any(i["kind"] != "code" for i in items):
            raise ValueError("strategy 9 needs a code task")
        tasks = [(s, it) for it in items]
        if workers > 1:
            with ThreadPoolExecutor(workers) as ex:
                list(ex.map(work, tasks))
        else:
            for t in tasks:
                work(t)
    return {"new_results": counts["new"], "errors": counts["errors"], "seconds": time.time() - t0}


def summarize(out_dir: str, project_n: Optional[int] = None, price_in: Optional[float] = None, price_out: Optional[float] = None) -> List[dict]:
    rows = [json.loads(l) for l in open(os.path.join(out_dir, "results.jsonl"), encoding="utf-8") if l.strip()]
    by: Dict[tuple, List[dict]] = {}
    for r in rows:
        by.setdefault((r["strategy"], r["model"], r["task"]), []).append(r)
    out = []
    for (s, m, t), rs in sorted(by.items()):
        n = len(rs)
        row = {"strategy": s, "model": m, "task": t, "n_items": n, "accuracy": sum(r["correct"] for r in rs) / n,
               "calls_per_item": sum(r["calls"] for r in rs) / n, "prompt_tokens_per_item": sum(r["prompt_tokens"] for r in rs) / n,
               "completion_tokens_per_item": sum(r["completion_tokens"] for r in rs) / n, "latency_sum_per_item_s": sum(r["latency_sum"] for r in rs) / n}
        if project_n:
            row["projected_calls"] = row["calls_per_item"] * project_n
            row["projected_hours_serial"] = row["latency_sum_per_item_s"] * project_n / 3600
            if price_in is not None and price_out is not None:
                row["projected_cost_usd"] = (row["prompt_tokens_per_item"] * price_in + row["completion_tokens_per_item"] * price_out) * project_n / 1e6
        out.append(row)
    return out


def export_pool(store: Store, model: str, items: List[dict], path: str, k: int = 16) -> int:
    """Write the S1/S2 calls in the `cme baseline` cache format so `cme report --pool` can read them. Non-code tasks only.
    The gold label is the literal 'G'; a correct response gets answer 'G', a wrong one its own normalised answer plus '_wrong'."""
    n = 0
    with open(path, "w", encoding="utf-8") as fh:
        for it in items:
            if it["kind"] == "code":
                continue
            recs = [("greedy", 0, store.d.get("greedy|%s|%s" % (model, it["id"])))] + [("sample", i, store.d.get("pool|%s|%s|%d" % (model, it["id"], i))) for i in range(k)]
            for arm, i, r in recs:
                if r is None:
                    continue
                ok = T.score(it, r["text"])
                fh.write(json.dumps({"item": it["id"], "arm": arm, "idx": i, "gold": "G", "answer": "G" if ok else (ans_of(it, r) or "?") + "_wrong", "correct": ok,
                                     "prompt_tokens": r["prompt_tokens"], "completion_tokens": r["completion_tokens"], "reasoning_tokens": None,
                                     "latency": r["latency"], "model": model}) + "\n")
                n += 1
    return n


def write_manifest(path: str, a, items: List[dict]) -> None:
    """Append one manifest entry: what was run, with which preregistration file (SHA-256), git commit, server version, and item ids."""
    import subprocess
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    prereg = os.path.join(root, "docs", "PREREGISTRATION.md")
    sha = hashlib.sha256(open(prereg, "rb").read()).hexdigest() if os.path.exists(prereg) else None
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, timeout=10).stdout.strip() or None
        dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", "docs/PREREGISTRATION.md", "code"], cwd=root, capture_output=True, text=True, timeout=10).stdout.strip())
    except Exception:
        commit, dirty = None, None
    try:
        with urllib.request.urlopen("http://localhost:11434/api/version", timeout=5) as r:
            ver = json.loads(r.read()).get("version")
    except Exception:
        ver = None
    from .baseline import ollama_digest
    entry = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "preregistration_sha256": sha, "git_commit": commit, "code_or_prereg_uncommitted_changes": dirty,
             "ollama_version": ver, "model": a.model, "model_digest": ollama_digest(a.model), "task": a.task, "n_items": len(items),
             "item_ids_sha256": hashlib.sha256("|".join(i["id"] for i in items).encode()).hexdigest(), "strategies": a.strategies, "k": a.k, "agents": a.agents,
             "rounds": a.rounds, "seed": a.seed, "max_tokens": a.max_tokens, "think_tokens": a.think_tokens, "workers": a.workers, "out": a.out}
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="cme-experiment", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--model", required=True)
    r.add_argument("--models", default=None, help="comma-separated model list for strategy 6")
    r.add_argument("--task", required=True, choices=list(T.SOURCES) + ["hidden_profile"])
    r.add_argument("--n", type=int, default=50)
    r.add_argument("--stratify", action="store_true", help="draw items round-robin over categories/subjects")
    r.add_argument("--num-ctx", type=int, default=8192, help="Ollama context length; must exceed prompt + max tokens")
    r.add_argument("--strategies", default="1")
    r.add_argument("--out", required=True)
    r.add_argument("--k", type=int, default=16)
    r.add_argument("--agents", type=int, default=5)
    r.add_argument("--rounds", type=int, default=3)
    r.add_argument("--seed", type=int, default=0)
    r.add_argument("--max-tokens", type=int, default=2048)
    r.add_argument("--think-tokens", type=int, default=8192)
    r.add_argument("--workers", type=int, default=1, help="concurrent items (Ollama serves them in parallel slots)")
    r.add_argument("--price-in", type=float, default=0.0, help="USD per million input tokens (0.0 for local models)")
    r.add_argument("--price-out", type=float, default=0.0)
    r.add_argument("--think", action="store_true", help="pass think=true on ordinary calls (reasoning models then report thinking separately)")
    r.add_argument("--manifest", default=None, help="write a run manifest (preregistration hash, git commit, versions) to this path")
    r.add_argument("--evidence", choices=["split", "shared"], default="split", help="split-evidence tasks: each agent sees its own view (split) or all evidence (shared)")
    tr = sub.add_parser("trace", help="write the round-by-round JSONL of a debate strategy for `cme dynamics` (reads the cache, never calls a model)")
    tr.add_argument("--model", required=True)
    tr.add_argument("--task", required=True, choices=list(T.SOURCES) + ["hidden_profile"])
    tr.add_argument("--n", type=int, default=50)
    tr.add_argument("--strategy", required=True, help="S4, S4v, S5, S12 or S12u")
    tr.add_argument("--out", required=True, help="the cell directory of the run")
    tr.add_argument("--agents", type=int, default=5)
    tr.add_argument("--evidence", choices=["split", "shared"], default="split")
    tr.add_argument("--dest", required=True)
    rs = sub.add_parser("rescore", help="recompute results.jsonl from cached calls (never calls a model)")
    rs.add_argument("--model", required=True)
    rs.add_argument("--task", required=True, choices=list(T.SOURCES) + ["hidden_profile"])
    rs.add_argument("--n", type=int, default=50)
    rs.add_argument("--strategies", default="1")
    rs.add_argument("--out", required=True)
    rs.add_argument("--k", type=int, default=16)
    rs.add_argument("--agents", type=int, default=5)
    rs.add_argument("--rounds", type=int, default=3)
    s = sub.add_parser("summary")
    s.add_argument("--out", required=True)
    s.add_argument("--project-n", type=int, default=None)
    s.add_argument("--price-in", type=float, default=None)
    s.add_argument("--price-out", type=float, default=None)
    a = ap.parse_args(argv)
    if a.cmd == "trace":
        from .verified_debate import export_trace
        n_rows = export_trace(a.out, load_items(a.task, a.n, evidence=a.evidence), a.strategy, a.model, a.agents, a.dest)
        print("wrote %d agent-round records to %s" % (n_rows, a.dest))
        return 0
    if a.cmd == "summary":
        for row in summarize(a.out, a.project_n, a.price_in, a.price_out):
            print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}))
        return 0
    if a.cmd == "rescore":
        class NoCall:
            def chat(self, *x, **y):
                raise RuntimeError("rescore must not call a model: a call is missing from the cache")
        rp = os.path.join(a.out, "results.jsonl")
        if os.path.exists(rp):
            os.replace(rp, rp + ".bak")
        ctx = Ctx(NoCall(), Store(os.path.join(a.out, "calls.jsonl")), a.model, k=a.k, agents=a.agents, rounds=a.rounds)
        print(json.dumps(run(ctx, T.load_task(a.task, a.n), [int(x) for x in a.strategies.split(",")], a.out, progress=None)))
        return 0
    items = load_items(a.task, a.n, stratify=a.stratify, evidence=a.evidence)
    os.makedirs(a.out, exist_ok=True)
    ctx = Ctx(OllamaClient(num_ctx=a.num_ctx), Store(os.path.join(a.out, "calls.jsonl")), a.model, a.models.split(",") if a.models else None, a.k, a.agents, a.rounds, a.seed,
              max_tokens=a.max_tokens, think_tokens=a.think_tokens, price_in=a.price_in, price_out=a.price_out, think_default=a.think)
    if a.manifest:
        write_manifest(a.manifest, a, items)
    print(json.dumps(run(ctx, items, [int(x) for x in a.strategies.split(",")], a.out, workers=a.workers)))
    return 0



from . import verified_debate as _vd  # noqa: E402  (registers strategy 12; imported last because verified_debate imports this module lazily)
STRATS[12] = _vd.s12_verified_debate
STRATS[13] = _vd.s13_shuffled_debate

if __name__ == "__main__":
    sys.exit(main())
