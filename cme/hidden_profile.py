"""cme hidden-profile: a configurable generator for the synthetic split-evidence (hidden-profile) task, with a built-in validity checker.

Design (Stasser and Titus 1985): four candidates are scored on `criteria` equally weighted criteria. `criteria - split` criteria are shared by all agents and favour a
decoy candidate; the `split` other criteria favour the target and are divided among `agents` agents, each of whom sees the shared criteria and `ceil(split / agents)`
of the split ones. Every single view then favours the decoy, and only the pooled evidence favours the target. Scores run from `low = 2` to `low + margin`.

With the default knobs (agents 5, criteria 10, split 6, margin 3, text format) the prompts, views and gold answers are identical to `cme.tasks.hidden_profile` (same seed, same random stream; `meta` has extra keys),
which is the task behind the released 500-item file.

Validity checks, computed from the generated scores (not from the construction): in every individual view the decoy has the strictly highest total of the four
candidates; on the pooled evidence the target has the strictly highest total; every split criterion appears in at least one view. Infeasible knobs are rejected
before generation: the shared criteria must outnumber the split criteria in one view (`criteria - split > ceil(split / agents)`) and the split criteria must outnumber
the shared ones (`split > criteria - split`), and `margin` must be at least 2.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Optional

NAMES = ["Avery", "Blake", "Casey", "Drew"]
LOW = 2


def check_knobs(agents: int, criteria: int, split: int, margin: int) -> None:
    if agents < 2:
        raise ValueError("agents must be at least 2")
    if margin < 2:
        raise ValueError("margin must be at least 2")
    if not 1 <= split < criteria:
        raise ValueError("split must satisfy 1 <= split < criteria")
    shared, view = criteria - split, math.ceil(split / agents)
    if shared <= view:
        raise ValueError("infeasible: the decoy cannot lead a single view; need criteria - split (%d) > ceil(split / agents) (%d)" % (shared, view))
    if split <= shared:
        raise ValueError("infeasible: the target cannot lead the pooled evidence; need split (%d) > criteria - split (%d)" % (split, shared))


def _scores_text(sc, js):
    return "\n".join("%s on %s: %d" % (NAMES[c], "criterion %d" % (j + 1), sc[c][j]) for j in js for c in range(4))


def _scores_numeric(sc, js):
    rows = ["criterion," + ",".join(NAMES)]
    rows += ["%d," % (j + 1) + ",".join(str(sc[c][j]) for c in range(4)) for j in js]
    return "\n".join(rows)


def generate(n: int, agents: int = 5, criteria: int = 10, split: int = 6, margin: int = 3, seed: int = 42, fmt: str = "text") -> List[dict]:
    """Return n items {id, task, prompt, gold, kind, meta, views}. See the module docstring."""
    if fmt not in ("text", "numeric"):
        raise ValueError("fmt must be 'text' or 'numeric'")
    check_knobs(agents, criteria, split, margin)
    shared, view = criteria - split, math.ceil(split / agents)
    high, cap = LOW + margin, min(LOW + margin - 2, 4)
    rng = random.Random(seed)
    out: List[dict] = []
    while len(out) < n:
        target, decoy = rng.sample(range(4), 2)
        sc = [[rng.randint(2, 4) for _ in range(criteria)] for _ in range(4)]
        for j in range(shared):                       # shared criteria: the decoy leads clearly
            for c in range(4):
                sc[c][j] = min(sc[c][j], cap)
            sc[decoy][j] = high
            sc[target][j] = LOW
        for j in range(shared, criteria):             # split criteria: the target leads
            for c in range(4):
                sc[c][j] = min(sc[c][j], cap)
            sc[target][j] = high
            sc[decoy][j] = LOW
        tot = [sum(r) for r in sc]
        if sorted(tot)[-1] == sorted(tot)[-2] or tot.index(max(tot)) != target:
            continue
        shown = _scores_text if fmt == "text" else _scores_numeric
        head = ("A committee must pick one of four candidates (%s) using %d equally weighted criteria, each scored %d to %d. The best candidate has the highest total score.\n\n"
                % (", ".join(NAMES), criteria, 1, high))
        tail = "\n\nWhich candidate has the highest total over all %d criteria? Give the name." % criteria
        full = head + "All scores:\n" + shown(sc, range(criteria)) + tail
        order = list(range(shared, criteria))
        rng.shuffle(order)
        views = []
        for a in range(agents):
            mine = sorted(order[(view * a + k) % split] for k in range(view))
            views.append(head + "You see only part of the evidence. Scores you can see:\n" + shown(sc, list(range(shared)) + mine) +
                         "\n\nOther committee members see the other criteria. Which candidate has the highest total over all %d criteria? Give the name." % criteria)
        out.append({"id": "hp%04d" % len(out), "task": "hidden_profile", "prompt": full, "gold": NAMES[target], "kind": "name",
                    "meta": {"synthetic": True, "totals": tot, "decoy": NAMES[decoy], "knobs": dict(agents=agents, criteria=criteria, split=split, margin=margin, seed=seed, fmt=fmt)},
                    "views": views})
    return out


def _parse_view(text: str, fmt: str, criteria: int):
    """Recover {criterion_index: {name: score}} from a prompt or view, in either format."""
    got: Dict[int, Dict[str, int]] = {}
    if fmt == "text":
        import re
        for name, j, s in re.findall(r"(\w+) on criterion (\d+): (\d+)", text):
            got.setdefault(int(j) - 1, {})[name] = int(s)
    else:
        for line in text.splitlines():
            parts = line.split(",")
            if len(parts) == 5 and parts[0].isdigit():
                got[int(parts[0]) - 1] = dict(zip(NAMES, map(int, parts[1:])))
    return got


def validate(items: List[dict]) -> Dict[str, int]:
    """Check each item from its prompt text: decoy strictly leads every view, target strictly leads the pooled evidence, every split criterion is seen. Returns counts."""
    bad = dict(items=len(items), decoy_not_leading_a_view=0, target_not_leading_pooled=0, uncovered_split_criteria=0)
    for it in items:
        k = it["meta"]["knobs"]
        fmt = k["fmt"] if "fmt" in k else "text"
        full = _parse_view(it["prompt"], fmt, k["criteria"])
        decoy, target = it["meta"]["decoy"], it["gold"]
        tot = {nm: sum(full[j][nm] for j in full) for nm in NAMES}
        best = sorted(tot.values())[-1]
        if not (tot[target] == best and list(tot.values()).count(best) == 1):
            bad["target_not_leading_pooled"] += 1
        seen = set()
        shared = k["criteria"] - k["split"]
        view_bad = False
        for v in it["views"]:
            part = _parse_view(v, fmt, k["criteria"])
            seen |= {j for j in part if j >= shared}
            vt = {nm: sum(part[j][nm] for j in part) for nm in NAMES}
            vb = sorted(vt.values())[-1]
            if not (vt[decoy] == vb and list(vt.values()).count(vb) == 1):
                view_bad = True
        bad["decoy_not_leading_a_view"] += view_bad
        bad["uncovered_split_criteria"] += len(set(range(shared, k["criteria"])) - seen) > 0
    return bad


def valid(counts: Dict[str, int]) -> bool:
    return not any(v for k, v in counts.items() if k != "items")
