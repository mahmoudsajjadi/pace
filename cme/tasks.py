"""Task loaders and scorers for the controlled experiment (Phase 2 pilots).

Data come from the public Hugging Face datasets-server JSON API (no parquet reader needed) and are cached under
data/experiments/<task>.jsonl with a provenance header. Subsets are drawn with a fixed seed (42) from the filtered pool so a run is
reproducible. Items share one schema:
    {"id", "task", "prompt", "gold", "kind": "mc" | "num" | "text" | "code", "meta", "views": optional list of agent-specific prompts}
`views` is used only by the split-evidence positive control, where each agent sees part of the evidence.

Substitutions to disclose: plain MBPP (the `test_list` asserts, 500 test items) stands in for MBPP+; the positive-control items are
synthetic (generated here, seed 42), they are not a published benchmark.
"""
from __future__ import annotations

import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data", "experiments")
API = "https://datasets-server.huggingface.co/rows"
LETTERS = "ABCDEFGHIJ"

SOURCES = {
    "mmlu_pro": ("TIGER-Lab/MMLU-Pro", "default", "test"),
    "math500_l45": ("HuggingFaceH4/MATH-500", "default", "test"),
    "musique_4hop": ("bdsaglam/musique", "answerable", "validation"),
    "mbpp": ("google-research-datasets/mbpp", "full", "test"),
    "gsm8k": ("openai/gsm8k", "main", "test"),
}


def _get(dataset: str, config: str, split: str, offset: int, length: int) -> List[dict]:
    q = urllib.parse.urlencode({"dataset": dataset, "config": config, "split": split, "offset": offset, "length": length})
    for attempt in range(8):
        try:
            with urllib.request.urlopen(API + "?" + q, timeout=60) as r:
                return [x["row"] for x in json.loads(r.read())["rows"]]
        except urllib.error.HTTPError as e:
            time.sleep(min(120, float(e.headers.get("Retry-After", 0) or 0) or 20 * (attempt + 1)))   # 429 rate limit: back off
        except Exception:
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("datasets-server unavailable for %s offset %d" % (dataset, offset))


def _fetch_all(dataset: str, config: str, split: str, total: int) -> List[dict]:
    rows: List[dict] = []
    for off in range(0, total, 100):
        rows += _get(dataset, config, split, off, min(100, total - off))
    return rows


def _mc_prompt(q: str, opts: List[str]) -> str:
    return q.strip() + "\n\nOptions:\n" + "\n".join("%s. %s" % (LETTERS[i], o) for i, o in enumerate(opts)) + "\n\nGive the letter of the correct option."


def load_task(task: str, n: int, seed: int = 42, refresh: bool = False, stratify: bool = False) -> List[dict]:
    """Return n items for a task (deterministic subset). Fetches and caches the filtered pool on first use."""
    if task == "hidden_profile":
        return hidden_profile(n, seed)
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, task + ".jsonl")
    if refresh or not os.path.exists(path):
        ds, cfg, sp = SOURCES[task]
        if task == "mmlu_pro":
            starts = sorted(random.Random(seed).sample(range(0, 12000, 100), 40))   # forty seeded 100-row blocks over the whole split (about 4,000 rows); the split is ordered by category, so one block is one category and 40 blocks cover all of them
            rows = []
            for st in starts:
                rows += _get(ds, cfg, sp, st, 100)
                time.sleep(0.5)   # stay under the datasets-server rate limit
            items = [{"id": "mmlu%05d" % r["question_id"], "task": task, "prompt": _mc_prompt(r["question"], r["options"]), "gold": r["answer"],
                      "kind": "mc", "meta": {"category": r["category"], "n_options": len(r["options"])}} for r in rows]
        elif task == "math500_l45":
            rows = [r for r in _fetch_all(ds, cfg, sp, 500) if r["level"] in (4, 5)]
            items = [{"id": r["unique_id"], "task": task, "prompt": r["problem"].strip(), "gold": r["answer"], "kind": "num",
                      "meta": {"level": r["level"], "subject": r["subject"]}} for r in rows]
        elif task == "musique_4hop":
            rows = [r for r in _fetch_all(ds, cfg, sp, 2417) if str(r["id"]).startswith("4hop")]
            items = []
            for r in rows:
                ctx = "\n\n".join("[%s] %s" % (p["title"], p["paragraph_text"]) for p in r["paragraphs"])
                items.append({"id": r["id"], "task": task, "prompt": "Paragraphs:\n" + ctx + "\n\nQuestion: " + r["question"] + "\nAnswer with a short phrase.",
                              "gold": [r["answer"]] + list(r.get("answer_aliases") or []), "kind": "text", "meta": {}})
        elif task == "gsm8k":
            rows = _fetch_all(ds, cfg, sp, 1319)
            items = [{"id": "gsm%04d" % i, "task": task, "prompt": r["question"].strip(), "gold": r["answer"].split("####")[-1].strip().replace(",", ""), "kind": "num", "meta": {}}
                     for i, r in enumerate(rows)]
        elif task == "mbpp":
            rows = _fetch_all(ds, cfg, sp, 500)
            items = [{"id": "mbpp%d" % r["task_id"], "task": task,
                      "prompt": r["text"].strip() + "\nYour code must pass this test:\n" + r["test_list"][0] + "\nReturn only the Python function in a ```python block.",
                      "gold": {"tests": r["test_list"], "setup": r["test_setup_code"]}, "kind": "code", "meta": {}} for r in rows]
        else:
            raise ValueError("unknown task " + task)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"_provenance": {"source": SOURCES[task], "api": API, "fetched": time.strftime("%Y-%m-%d"), "pool_size": len(items), "seed": seed}}) + "\n")
            for it in items:
                fh.write(json.dumps(it) + "\n")
    items = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip() and not l.startswith('{"_provenance"')]
    random.Random(seed).shuffle(items)
    if stratify:   # round-robin over categories (MMLU-Pro category, MATH subject) in the seeded order, so each stratum contributes about equally
        key = lambda it: str(it["meta"].get("category") or it["meta"].get("subject") or "")
        groups = {}
        for it in items:
            groups.setdefault(key(it), []).append(it)
        picked, i = [], 0
        while len(picked) < n and any(i < len(g) for g in groups.values()):
            picked += [g[i] for _, g in sorted(groups.items()) if i < len(g)]
            i += 1
        return picked[:n]
    return items[:n]


# ----------------------------------------------------------------------------- scoring
def _norm_num(s: str) -> str:
    s = str(s).strip().strip("$").replace("\\!", "").replace("\\,", "").replace("\\left", "").replace("\\right", "").replace("dfrac", "frac").replace("tfrac", "frac")
    s = re.sub(r"\\text\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\boxed\{(.*)\}", r"\1", s)
    s = s.replace("\\$", "").replace("$", "").replace(" ", "").rstrip(".").lower()
    s = re.sub(r"^(-?\d+)/(\d+)$", r"\\frac{\1}{\2}", s)
    s = re.sub(r"^(-?\d+)\.0+$", r"\1", s)
    s = re.sub(r"(degrees?|units?)$", "", s)
    s = s.replace("^{\\circ}", "").replace("^\\circ", "").replace("\\%", "").replace("%", "")
    return s.replace(",", "") if re.fullmatch(r"-?[\d,]+(\.\d+)?", s) else s


def _norm_text(s: str) -> str:
    s = re.sub(r"\b(a|an|the)\b", " ", str(s).lower())
    return " ".join(re.sub(r"[^\w\s]", "", s).split())


_ANS = re.compile(r"answer\s*[:=]\s*(.+)", re.I)
_CONF = re.compile(r"confidence\s*[:=]\s*(\d+(?:\.\d+)?)", re.I)


BOXED = "\\boxed{"


def last_boxed(text: str) -> str:
    """Contents of the last boxed{...} expression (brace-balanced), or ''."""
    text = text or ""
    i = text.rfind(BOXED)
    if i < 0:
        return ""
    start = i + len(BOXED)
    j, depth = start, 1
    while j < len(text) and depth:
        depth += {"{": 1, "}": -1}.get(text[j], 0)
        j += 1
    return text[start: j - 1] if depth == 0 else ""


_IS = re.compile(r"answer is:?\s*\$?\(?([^\n$]+)", re.I)


def parse_answer(text: str) -> str:
    """Final 'Answer:' payload (first line of it); else the last boxed content; else the payload of 'the answer is ...'; else ''."""
    m = _ANS.findall(text or "")
    if m:
        got = m[-1].strip().split("\n")[0].strip()
        return last_boxed(got) or got
    return last_boxed(text) or ((_IS.findall(text or "") or [""])[-1].strip().rstrip(".)"))


def parse_confidence(text: str) -> Optional[float]:
    m = _CONF.findall(text or "")
    return min(100.0, max(0.0, float(m[-1]))) / 100.0 if m else None


def extract_code(text: str) -> str:
    m = re.findall(r"```(?:python)?\n(.*?)```", text or "", re.S)
    return m[-1] if m else (text or "")


def run_tests(code: str, tests: List[str], setup: str = "", timeout: float = 10.0) -> bool:
    """Execute generated code plus the asserts in a separate Python process with a timeout (no sandbox beyond that; run on a trusted dev machine)."""
    src = (setup or "") + "\n" + code + "\n" + "\n".join(tests) + "\n"
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.py")
        open(p, "w", encoding="utf-8").write(src)
        try:
            return subprocess.run([sys.executable, "-I", p], cwd=d, capture_output=True, timeout=timeout).returncode == 0
        except subprocess.TimeoutExpired:
            return False


def normalize_answer(item: dict, ans: str) -> str:
    k = item["kind"]
    if k == "mc":
        m = re.search(r"\b([A-J])\b", (ans or "").upper())
        return m.group(1) if m else ""
    if k == "num":
        return _norm_num(ans)
    if k == "text":
        return _norm_text(ans)
    if k == "name":
        m = re.search(r"\b(avery|blake|casey|drew)\b", (ans or "").lower())
        return m.group(1) if m else ""
    return (ans or "").strip()


def score(item: dict, ans_text: str) -> bool:
    """Is a response correct? For code, ans_text is the full response (code is extracted and run)."""
    if item["kind"] == "code":
        return run_tests(extract_code(ans_text), item["gold"]["tests"], item["gold"].get("setup", ""))
    a = normalize_answer(item, parse_answer(ans_text))
    g = item["gold"]
    if item["kind"] == "text":
        return a != "" and any(a == _norm_text(x) for x in g)
    if item["kind"] == "num":
        return a != "" and a == _norm_num(g)
    if item["kind"] == "name":
        return a == str(g).lower()
    return a == str(g).strip().upper()


# ----------------------------------------------------------------------------- positive control
def hidden_profile(n: int, seed: int = 42, n_agents: int = 5) -> List[dict]:
    """Synthetic split-evidence task (hidden-profile design, Stasser and Titus 1985).

    Four candidates are scored 1-5 on 10 criteria with equal weights; the correct choice has the highest total. Criteria 1-4 are shared
    (every agent sees them) and favour a decoy; criteria 5-10 are split so that each agent sees only two of the six and the pooled
    total favours the target. A single agent shown all evidence (`prompt`) can compute the answer; one agent's `views[i]` cannot,
    and independent voting over views is expected to favour the decoy. Generated, not published: report it as synthetic."""
    rng = random.Random(seed)
    names = ["Avery", "Blake", "Casey", "Drew"]
    out = []
    while len(out) < n:
        target, decoy = rng.sample(range(4), 2)
        sc = [[rng.randint(2, 4) for _ in range(10)] for _ in range(4)]
        for j in range(4):                     # shared criteria: the decoy leads clearly
            for c in range(4):
                sc[c][j] = min(sc[c][j], 3)
            sc[decoy][j] = 5
            sc[target][j] = 2
        for j in range(4, 10):                 # split criteria: the target leads
            for c in range(4):
                sc[c][j] = min(sc[c][j], 3)
            sc[target][j] = 5
            sc[decoy][j] = 2
        tot = [sum(r) for r in sc]
        if sorted(tot)[-1] == sorted(tot)[-2] or tot.index(max(tot)) != target:
            continue
        crit = ["criterion %d" % (j + 1) for j in range(10)]
        facts = lambda js: "\n".join("%s on %s: %d" % (names[c], crit[j], sc[c][j]) for j in js for c in range(4))
        head = "A committee must pick one of four candidates (Avery, Blake, Casey, Drew) using 10 equally weighted criteria, each scored 1 to 5. The best candidate has the highest total score.\n\n"
        tail = "\n\nWhich candidate has the highest total over all 10 criteria? Give the name."
        full = head + "All scores:\n" + facts(range(10)) + tail
        order = list(range(4, 10))
        rng.shuffle(order)
        views = []
        for a in range(n_agents):
            mine = sorted([order[(2 * a) % 6], order[(2 * a + 1) % 6]])
            views.append(head + "You see only part of the evidence. Scores you can see:\n" + facts(list(range(4)) + mine) +
                         "\n\nOther committee members see the other criteria. Which candidate has the highest total over all 10 criteria? Give the name.")
        out.append({"id": "hp%04d" % len(out), "task": "hidden_profile", "prompt": full, "gold": names[target], "kind": "name", "meta": {"synthetic": True, "totals": tot},
                    "views": views})
    return out
