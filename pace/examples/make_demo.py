"""Generate the SYNTHETIC demo data used by the quickstart notebook and tests: demo_pool.jsonl and demo_run.jsonl.

Nothing here comes from a model. Items have a hidden per-item success probability; sampled completions are correct with that probability;
three illustrative "systems" are drawn from fixed rules so the report has something to compare. The numbers say nothing about any real method.
Run: python code/cme/examples/make_demo.py   (seed 7, 40 items, 8 samples per item)
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(7)
N, K = 40, 8
p_item = rng.beta(2.0, 2.0, N)
pool, run = [], []
for i in range(N):
    item = "demo%02d" % i
    tok_p, tok_c = int(rng.integers(60, 90)), int(rng.integers(180, 320))

    def rec(arm, idx, ok):
        return {"item": item, "arm": arm, "idx": idx, "gold": "G", "answer": "G" if ok else "w%d" % int(rng.integers(0, 3)), "correct": bool(ok), "prompt_tokens": tok_p,
                "completion_tokens": int(tok_c * rng.uniform(0.8, 1.2)), "reasoning_tokens": None, "latency": float(rng.uniform(2, 6)), "model": "synthetic"}
    pool.append(rec("greedy", 0, rng.random() < p_item[i] * 0.95))
    pool += [rec("sample", j, rng.random() < p_item[i]) for j in range(K)]
    # three illustrative systems: five-call debate with a small boost, three-call voting on fresh samples, one longer single call
    for system, calls, boost, mult in (("debate", 5, 0.02, 1.9), ("vote3", 3, 0.0, 1.0), ("long_call", 1, 0.03, 4.0)):
        ok = rng.random() < min(0.98, p_item[i] + boost)
        for c in range(calls):
            run.append({"system": system, "item": item, "prompt_tokens": int(tok_p * (1 + 0.5 * (system == "debate"))), "completion_tokens": int(tok_c * mult / calls * rng.uniform(0.9, 1.1)),
                        "n_completions": 1, "start": 0.0, "end": float(rng.uniform(3, 8))})
        run.append({"system": system, "item": item, "correct": bool(ok)})
with open(os.path.join(HERE, "demo_pool.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("".join(json.dumps(r) + "\n" for r in pool))
with open(os.path.join(HERE, "demo_run.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("".join(json.dumps(r) + "\n" for r in run))
print("wrote demo_pool.jsonl (%d rows) and demo_run.jsonl (%d rows), synthetic" % (len(pool), len(run)))
