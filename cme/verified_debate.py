"""Route II harness and debate-trace export.

s12_verified_debate (strategy 12): numeric tasks only. Every response must end with 'Expression: ...', 'Answer: ...' and 'Confidence: ...'. Two debates start from the same round-1 responses:
  S12u  ungated: agents update freely (the same prompts as S12);
  S12   gated: an agent's changed answer is accepted only if cme.verifier accepts that response (the expression evaluates to the stated answer); otherwise the agent keeps its
        previous accepted response. The gate is deterministic and runs no model-written code.
The only difference between S12u and S12 is the gate, so the change in transition rates between them (right-to-wrong in particular) is attributable to the verifier. The verifier checks
arithmetic, not the reading of the problem (see cme.verifier), so it is partial.
Results carry round_answers and round_tokens per agent and round, which export_trace writes as the JSONL that `cme dynamics` reads.
"""
from __future__ import annotations

import json
import os
from typing import List, Optional

VSOLVE = ("{q}\n\nThink step by step. Finish with three final lines: 'Expression: <one arithmetic expression using only numbers and + - * / ( ) that computes the answer from the "
          "quantities in the problem>', 'Answer: <answer>' and 'Confidence: <0-100>'.")
VDEBATE = ("{q}\n\nYour previous response:\n{own}\n\nOther agents responded:\n{peers}\n\nUse their reasoning as additional information, but verify it yourself. Give your updated solution. "
           "Finish with three final lines: 'Expression: <one arithmetic expression using only numbers and + - * / ( )>', 'Answer: <answer>' and 'Confidence: <0-100>'.")


def _round1(ctx, item):
    return [ctx.call("V1|%s|%s|%d" % (ctx.model, item["id"], i), ctx.model, VSOLVE.format(q=item["prompt"]), ctx.temperature, think=ctx.think_default) for i in range(ctx.agents)]


def _debate(ctx, item, name, r1, gated):
    from . import experiment as E
    from .verifier import verify
    state = list(r1)
    answers = [[E.ans_of(item, r) for r in state]]
    tokens = [[[r.get("prompt_tokens"), r.get("completion_tokens")] for r in state]]
    rejected = changed = 0
    for rd in range(2, ctx.rounds + 1):
        texts = [r["text"] for r in state]
        nxt, tok = [], []
        for j in range(len(state)):
            peers = E._peers(ctx, texts, j, False, None)
            new = ctx.call("%s|%s|%s|r%d|a%d" % (name, ctx.model, item["id"], rd, j), ctx.model, VDEBATE.format(q=item["prompt"], own=E._tail(texts[j]), peers=peers), ctx.temperature,
                           think=ctx.think_default, comm_chars=len(peers))
            tok.append([new.get("prompt_tokens"), new.get("completion_tokens")])
            old_a, new_a = E.ans_of(item, state[j]), E.ans_of(item, new)
            if new_a != old_a:
                if gated and not verify(new["text"])[0]:
                    rejected += 1
                    nxt.append(state[j])
                    continue
                changed += 1
            nxt.append(new)
        state = nxt
        answers.append([E.ans_of(item, r) for r in state])
        tokens.append(tok)
    leaders, cr = E.vote(answers[-1], E._is_gold(item))
    return leaders, cr, {"round_answers": answers, "round_tokens": tokens, "rejected": rejected, "changed": changed}


def s12_verified_debate(ctx, item):
    from . import experiment as E
    if item["kind"] != "num":
        raise ValueError("strategy 12 needs a numeric task")
    r1 = _round1(ctx, item)
    base = list(ctx.used)
    lu, cu, eu = _debate(ctx, item, "S12u", r1, False)
    res_u = E._result(ctx, "S12u", item, cu, "|".join(lu), eu)
    ctx.used = list(base)
    lg, cg, eg = _debate(ctx, item, "S12", r1, True)
    res_g = E._result(ctx, "S12", item, cg, "|".join(lg), eg)
    return [res_u, res_g]


def export_trace(out_dir: str, items: List[dict], strategy: str, model: str, agents: int, path: str) -> int:
    """Write one JSONL record per agent answer and round for every finished item of `strategy`: item, agent, round, correct, prompt_tokens, completion_tokens, strategy.
    Strategies S12 and S12u use the accepted answers stored in their results; S4, S4v, S5 and S7 are reconstructed from the cached calls (round 1 is the pool sample or the agent's view)."""
    from . import experiment as E
    by_id = {it["id"]: it for it in items}
    store = E.Store(os.path.join(out_dir, "calls.jsonl"))
    n = 0
    with open(path, "w", encoding="utf-8") as fh:
        for line in open(os.path.join(out_dir, "results.jsonl"), encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            if r["strategy"] != strategy or r["item"] not in by_id:
                continue
            item, gold = by_id[r["item"]], E._is_gold(by_id[r["item"]])
            rows = []
            if "round_answers" in r:
                for rd, (ans, tok) in enumerate(zip(r["round_answers"], r["round_tokens"]), 1):
                    for a, (an, (pt, ct)) in enumerate(zip(ans, tok)):
                        rows.append((a, rd, bool(gold(an)), pt, ct))
            else:
                rounds = max(int(k.split("|")[3][1:]) for k in r["keys"] if "|r" in k) if any("|r" in k for k in r["keys"]) else 1
                for a in range(agents):
                    for rd in range(1, rounds + 1):
                        if rd == 1:
                            key = ("r1v|%s|%s|%d" if item.get("views") else "pool|%s|%s|%d") % (model, item["id"], a)
                        else:
                            key = "%s|%s|%s|r%d|a%d" % (strategy, "+".join([model] * agents), item["id"], rd, a)      # the debate key names the model of every agent
                        rec = store.d.get(key)
                        if rec is None:
                            raise KeyError("call %s is not in the cache" % key)
                        rows.append((a, rd, bool(gold(E.ans_of(item, rec))), rec.get("prompt_tokens"), rec.get("completion_tokens")))
            for a, rd, ok, pt, ct in rows:
                rec = {"item": r["item"], "agent": a, "round": rd, "correct": ok, "strategy": strategy}
                if pt is not None and ct is not None:
                    rec["prompt_tokens"], rec["completion_tokens"] = pt, ct
                fh.write(json.dumps(rec) + "\n")
                n += 1
    return n


def _shuffle_sentences(body: str, q: str, j: int) -> str:
    """Peer message with its sentences in a deterministic random order (same words, same length, the reasoning order destroyed)."""
    import hashlib
    import random
    import re
    parts = [x for x in re.split(r"(?<=[.!?])\s+", body.strip()) if x]
    random.Random(int(hashlib.sha256(("%s|%d" % (body[:40], j)).encode()).hexdigest()[:8], 16)).shuffle(parts)
    return " ".join(parts)


def s13_shuffled_debate(ctx, item):
    """Debate whose peer messages have their sentences shuffled: the words and the length are kept, the argument order is not. Round 1 is the first `agents` pool samples."""
    from . import experiment as E
    leaders, cr, ex = E._debate(ctx, item, "S13", [ctx.model] * ctx.agents, E.round1(ctx, item, ctx.agents), False, False, peer_transform=_shuffle_sentences)
    return E._result(ctx, "S13", item, cr, "|".join(leaders), ex)

