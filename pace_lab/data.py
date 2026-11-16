"""pace_lab.data: benchmark loaders that save the item files and a manifest (ids + SHA-256 hashes) under data/pace_lab/.

Datasets (item schema as in cme.tasks: {id, task, prompt, gold, kind, meta[, views]}):
    mmlu_pro        TIGER-Lab/MMLU-Pro test split, 1,000 items stratified by category (proportional allocation, largest remainder), seed 2026
    math500_l45     HuggingFaceH4/MATH-500 test split, every item of level 4 or 5 (no sampling)
    hp_numeric / hp_nl                      hidden-profile, 500 synthetic items, seed 42, evidence as a numeric table / as prose
    hp_numeric_shared / hp_nl_shared        the shared-evidence twin of each: same scores and gold, but every agent sees ALL evidence (no hidden profile)

Source of real data: the public Hugging Face datasets-server JSON API (same endpoint as cme.tasks). The full raw pool is cached under
data/pace_lab/raw/ so a rebuild is offline and byte-identical. Nothing is fabricated: if the download fails, `build_*` raises and no item file is written.
Hidden-profile items are SYNTHETIC (meta.synthetic is true) and come from the existing generator (code/cme/hidden_profile.py, loaded read-only by
file path; code/pace/hidden_profile.py if the package was renamed). The natural-language rendering and the twin are made here from the generator's scores.

Manifest (data/pace_lab/manifest.json): per dataset the source, selection rule, seed, n, file name, file sha256, the ordered id list and an
item_sha256 map (sha256 of the canonical JSON of each item). `verify_manifest` re-hashes everything.

Command line:  python -m pace_lab.data build {mmlu_pro,math500_l45,hidden_profile,all} [--refresh] [--from-experiments-cache]   |   verify
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

CODE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(CODE_DIR)
DATA_DIR = os.path.join(ROOT, "data", "pace_lab")
HF_ROWS_API = "https://datasets-server.huggingface.co/rows"
LETTERS = "ABCDEFGHIJ"
SOURCES = {
    "mmlu_pro": ("TIGER-Lab/MMLU-Pro", "default", "test"),
    "math500_l45": ("HuggingFaceH4/MATH-500", "default", "test"),
}
RowFetcher = Callable[[str, str, str, int, int], Tuple[List[dict], int]]    # (dataset, config, split, offset, length) -> (rows, num_rows_total)


# ----------------------------------------------------------------------------- hashing and files
def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def item_hash(item: dict) -> str:
    return sha256_text(canonical_json(item))


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_jsonl(path: str, rows: Sequence[dict], header: Optional[dict] = None) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        if header is not None:
            fh.write(json.dumps({"_provenance": header}, ensure_ascii=False, sort_keys=True) + "\n")
        for r in rows:
            fh.write(canonical_json(r) + "\n")


def read_jsonl(path: str) -> List[dict]:
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rec = json.loads(line)
                if "_provenance" not in rec or len(rec) > 1:
                    out.append(rec)
    return out


def read_provenance(path: str) -> Optional[dict]:
    with open(path, encoding="utf-8") as fh:
        first = fh.readline()
    rec = json.loads(first) if first.strip() else {}
    return rec.get("_provenance") if len(rec) == 1 else None


# ----------------------------------------------------------------------------- manifest
def manifest_path(data_dir: Optional[str] = None) -> str:
    return os.path.join(data_dir or DATA_DIR, "manifest.json")


def load_manifest(data_dir: Optional[str] = None) -> dict:
    p = manifest_path(data_dir)
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    return {"schema": 1, "datasets": {}}


def register(name: str, items: List[dict], info: dict, data_dir: Optional[str] = None) -> dict:
    """Write data/pace_lab/<name>.jsonl and add its entry (ids, per-item sha256, file sha256, provenance) to manifest.json."""
    d = data_dir or DATA_DIR
    os.makedirs(d, exist_ok=True)
    fname = name + ".jsonl"
    path = os.path.join(d, fname)
    write_jsonl(path, items)
    entry = dict(info)
    entry.update({"file": fname, "n": len(items), "file_sha256": file_sha256(path), "ids": [it["id"] for it in items],
                  "item_sha256": {it["id"]: item_hash(it) for it in items}})
    if len(set(entry["ids"])) != len(entry["ids"]):
        raise ValueError("duplicate item ids in " + name)
    m = load_manifest(d)
    m["datasets"][name] = entry
    m["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    with open(manifest_path(d), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(m, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    return entry


def verify_manifest(data_dir: Optional[str] = None) -> List[str]:
    """Re-hash every file and item listed in the manifest. Returns a list of problems (empty = all good)."""
    d = data_dir or DATA_DIR
    problems: List[str] = []
    for name, e in load_manifest(d).get("datasets", {}).items():
        path = os.path.join(d, e["file"])
        if not os.path.isfile(path):
            problems.append("%s: file missing" % name)
            continue
        if file_sha256(path) != e["file_sha256"]:
            problems.append("%s: file hash differs" % name)
        items = read_jsonl(path)
        if [it["id"] for it in items] != e["ids"]:
            problems.append("%s: id list differs" % name)
        for it in items:
            if e["item_sha256"].get(it["id"]) != item_hash(it):
                problems.append("%s: item %s hash differs" % (name, it["id"]))
    return problems


def load_dataset(name: str, data_dir: Optional[str] = None, verify: bool = True) -> List[dict]:
    d = data_dir or DATA_DIR
    e = load_manifest(d)["datasets"][name]
    items = read_jsonl(os.path.join(d, e["file"]))
    if verify and [item_hash(i) for i in items] != [e["item_sha256"][i["id"]] for i in items]:
        raise ValueError("%s: items do not match the manifest hashes" % name)
    return items


# ----------------------------------------------------------------------------- Hugging Face rows API
def hf_fetcher(dataset: str, config: str, split: str, offset: int, length: int) -> Tuple[List[dict], int]:
    """One page from the datasets-server (max length 100), with retries; returns (rows, num_rows_total)."""
    q = urllib.parse.urlencode({"dataset": dataset, "config": config, "split": split, "offset": offset, "length": length})
    last = "unknown"
    for attempt in range(8):
        try:
            with urllib.request.urlopen(HF_ROWS_API + "?" + q, timeout=60) as r:
                data = json.loads(r.read())
            return [x["row"] for x in data["rows"]], int(data["num_rows_total"])
        except urllib.error.HTTPError as e:
            last = "HTTP %d" % e.code
            time.sleep(min(120, float(e.headers.get("Retry-After", 0) or 0) or 15 * (attempt + 1)))
        except Exception as e:                                  # noqa: BLE001
            last = type(e).__name__
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("datasets-server unavailable for %s offset %d (%s)" % (dataset, offset, last))


def fetch_split(dataset: str, config: str, split: str, fetcher: RowFetcher = hf_fetcher, page: int = 100, pause: float = 0.5,
                sleep: Callable[[float], None] = time.sleep) -> List[dict]:
    rows: List[dict] = []
    offset, total = 0, None
    while total is None or offset < total:
        got, total = fetcher(dataset, config, split, offset, page)
        if not got:
            break
        rows += got
        offset += len(got)
        if pause:
            sleep(pause)
    if total is not None and len(rows) != total:
        raise RuntimeError("fetched %d of %d rows from %s" % (len(rows), total, dataset))
    return rows


# ----------------------------------------------------------------------------- item builders
def mc_prompt(question: str, options: Sequence[str]) -> str:
    return question.strip() + "\n\nOptions:\n" + "\n".join("%s. %s" % (LETTERS[i], o) for i, o in enumerate(options)) + "\n\nGive the letter of the correct option."


def mmlu_pro_items(rows: Sequence[dict]) -> List[dict]:
    out = []
    for r in rows:
        opts = list(r["options"])
        if not 2 <= len(opts) <= 10 or r["answer"] not in LETTERS[:len(opts)]:
            raise ValueError("unexpected MMLU-Pro row %r" % r.get("question_id"))
        out.append({"id": "mmlu%05d" % r["question_id"], "task": "mmlu_pro", "prompt": mc_prompt(r["question"], opts), "gold": r["answer"], "kind": "mc",
                    "meta": {"category": r["category"], "n_options": len(opts), "question_id": r["question_id"], "src": r.get("src")}})
    return out


def math500_items(rows: Sequence[dict], levels=(4, 5)) -> List[dict]:
    return [{"id": r["unique_id"], "task": "math500_l45", "prompt": r["problem"].strip(), "gold": r["answer"], "kind": "num",
             "meta": {"level": r["level"], "subject": r["subject"]}} for r in rows if r["level"] in levels]


def allocate(counts: Dict[str, int], n: int) -> Dict[str, int]:
    """Proportional allocation of n draws over strata (largest remainder; ties by stratum name)."""
    total = sum(counts.values())
    if n > total:
        raise ValueError("cannot draw %d items from a pool of %d" % (n, total))
    quota = {k: n * c / total for k, c in counts.items()}
    base = {k: int(math.floor(q)) for k, q in quota.items()}
    left = n - sum(base.values())
    for k in sorted(counts, key=lambda k: (-(quota[k] - base[k]), k))[:left]:
        base[k] += 1
    return base


def stratified_sample(items: Sequence[dict], n: int, seed: int, key: Callable[[dict], str]) -> List[dict]:
    """n items stratified by key: proportional allocation, a seeded random.Random(seed).sample inside each stratum (strata in name order,
    pool in id order), returned in id order."""
    groups: Dict[str, List[dict]] = {}
    for it in sorted(items, key=lambda i: i["id"]):
        groups.setdefault(key(it), []).append(it)
    alloc = allocate({k: len(v) for k, v in groups.items()}, n)
    rng = random.Random(seed)
    picked: List[dict] = []
    for k in sorted(groups):
        picked += rng.sample(groups[k], alloc[k])
    return sorted(picked, key=lambda i: i["id"])


# ----------------------------------------------------------------------------- real-data builders
def _pool(name: str, fetcher: RowFetcher, data_dir: str, refresh: bool, pause: float, sleep) -> Tuple[List[dict], dict]:
    ds, cfg, sp = SOURCES[name]
    raw = os.path.join(data_dir, "raw", name + "_pool.jsonl")
    if os.path.isfile(raw) and not refresh:
        prov = read_provenance(raw) or {}
        return read_jsonl(raw), dict(prov, pool_file="raw/%s_pool.jsonl" % name, pool_sha256=file_sha256(raw))
    rows = fetch_split(ds, cfg, sp, fetcher, pause=pause, sleep=sleep)
    prov = {"source": [ds, cfg, sp], "api": HF_ROWS_API, "fetched": time.strftime("%Y-%m-%d"), "pool_rows": len(rows)}
    write_jsonl(raw, rows, prov)
    return rows, dict(prov, pool_file="raw/%s_pool.jsonl" % name, pool_sha256=file_sha256(raw))


def build_mmlu_pro(n: int = 1000, seed: int = 2026, fetcher: RowFetcher = hf_fetcher, data_dir: Optional[str] = None, refresh: bool = False,
                   pause: float = 0.5, sleep=time.sleep) -> dict:
    d = data_dir or DATA_DIR
    rows, prov = _pool("mmlu_pro", fetcher, d, refresh, pause, sleep)
    pool = mmlu_pro_items(rows)
    items = stratified_sample(pool, n, seed, key=lambda it: it["meta"]["category"])
    cats = {}
    for it in items:
        cats[it["meta"]["category"]] = cats.get(it["meta"]["category"], 0) + 1
    info = {"source": prov["source"], "selection": "stratified by category, proportional allocation (largest remainder), random.Random(seed).sample inside each stratum",
            "seed": seed, "pool_size": len(pool), "pool_file": prov["pool_file"], "pool_sha256": prov["pool_sha256"], "fetched": prov.get("fetched"),
            "per_category": dict(sorted(cats.items())), "synthetic": False}
    return register("mmlu_pro", items, info, d)


def build_math500_l45(fetcher: RowFetcher = hf_fetcher, data_dir: Optional[str] = None, refresh: bool = False, pause: float = 0.5, sleep=time.sleep) -> dict:
    d = data_dir or DATA_DIR
    rows, prov = _pool("math500_l45", fetcher, d, refresh, pause, sleep)
    items = sorted(math500_items(rows), key=lambda i: i["id"])
    info = {"source": prov["source"], "selection": "all MATH-500 items with level 4 or 5, id order (no sampling)", "seed": None, "pool_size": len(rows),
            "pool_file": prov["pool_file"], "pool_sha256": prov["pool_sha256"], "fetched": prov.get("fetched"), "synthetic": False,
            "per_level": {str(l): sum(1 for i in items if i["meta"]["level"] == l) for l in (4, 5)}}
    return register("math500_l45", items, info, d)


def items_from_experiments_cache(path: str) -> List[dict]:
    """Read an item file in the cme.tasks cache format (data/experiments/<task>.jsonl). That MMLU-Pro cache is a 4,000-row seeded sample, not the
    whole split, so a build from it is NOT the full-pool stratified draw; use only when the download is impossible and say so."""
    return read_jsonl(path)


# ----------------------------------------------------------------------------- hidden profile
def load_generator():
    """Load code/cme/hidden_profile.py (read-only, by file path; falls back to code/pace/ after a rename)."""
    for pkg in ("cme", "pace"):
        p = os.path.join(CODE_DIR, pkg, "hidden_profile.py")
        if os.path.isfile(p):
            spec = importlib.util.spec_from_file_location("pace_lab._hp_generator", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.__file_path__ = p
            return mod
    raise FileNotFoundError("hidden_profile.py not found under code/cme or code/pace")


NAMES = ("Avery", "Blake", "Casey", "Drew")
_NL_SENT = re.compile(r"On criterion (\d+), Avery scored (\d+), Blake scored (\d+), Casey scored (\d+) and Drew scored (\d+)\.")
_ALL_HEAD = "\n\nAll scores:\n"


def parse_numeric(text: str) -> Dict[int, Dict[str, int]]:
    got: Dict[int, Dict[str, int]] = {}
    for line in text.splitlines():
        parts = line.split(",")
        if len(parts) == 5 and parts[0].isdigit():
            got[int(parts[0])] = dict(zip(NAMES, map(int, parts[1:])))
    return got


def parse_nl(text: str) -> Dict[int, Dict[str, int]]:
    return {int(m[0]): dict(zip(NAMES, map(int, m[1:]))) for m in _NL_SENT.findall(text)}


def render_nl(scores: Dict[int, Dict[str, int]]) -> str:
    return " ".join("On criterion %d, Avery scored %d, Blake scored %d, Casey scored %d and Drew scored %d." % ((j,) + tuple(scores[j][n] for n in NAMES))
                    for j in sorted(scores))


def _to_nl(item: dict) -> dict:
    """Prose version of a numeric hidden-profile item: same scores, same gold, same intro and question sentences."""
    prompt = item["prompt"]
    i = prompt.index(_ALL_HEAD)
    head, rest = prompt[:i], prompt[i + len(_ALL_HEAD):]
    q = rest.rindex("\n\nWhich candidate")
    new_prompt = head + _ALL_HEAD + render_nl(parse_numeric(rest[:q])) + rest[q:]
    views = []
    for v in item["views"]:
        marker = "You see only part of the evidence. Scores you can see:\n"
        a = v.index(marker)
        b = v.index("\n\nOther committee members")
        views.append(v[:a + len(marker)] + render_nl(parse_numeric(v[a + len(marker):b])) + v[b:])
    return dict(item, prompt=new_prompt, views=views)


def _twin(item: dict) -> dict:
    """Shared-evidence twin: identical scores, gold and `prompt`, but every agent's view contains ALL the evidence."""
    shared = item["prompt"].replace("All scores:", "All committee members see the same evidence. Scores you can see:", 1)
    return dict(item, views=[shared for _ in item["views"]])


def _hp_label(item: dict, prefix: str, fmt: str, evidence: str, suffix: str) -> dict:
    base = item["id"]
    meta = dict(item["meta"], base_id=base, format=fmt, evidence=evidence, synthetic=True)
    if evidence == "shared":
        meta["twin_of"] = prefix + base[2:]
    return dict(item, id=prefix + base[2:] + suffix, meta=meta)


def validate_hidden_profile(items: Sequence[dict], parser: Callable[[str], Dict[int, Dict[str, int]]]) -> Dict[str, int]:
    """Check from the prompt text: gold strictly leads the pooled evidence; split items: decoy strictly leads every view, every split criterion is seen
    by some agent; shared twins: every view contains all criteria and gold strictly leads it."""
    bad = dict(items=len(items), target_not_leading_pooled=0, decoy_not_leading_a_view=0, uncovered_split_criteria=0, twin_view_incomplete=0)

    def leader(sc):
        tot = {n: sum(sc[j][n] for j in sc) for n in NAMES}
        best = max(tot.values())
        top = [n for n in NAMES if tot[n] == best]
        return top[0] if len(top) == 1 else None
    for it in items:
        k = it["meta"]["knobs"]
        full = parser(it["prompt"])
        if len(full) != k["criteria"] or leader(full) != it["gold"]:
            bad["target_not_leading_pooled"] += 1
        shared_n = k["criteria"] - k["split"]
        seen, view_bad = set(), False
        for v in it["views"]:
            part = parser(v)
            if it["meta"].get("evidence") == "shared":
                if len(part) != k["criteria"] or leader(part) != it["gold"]:
                    bad["twin_view_incomplete"] += 1
                continue
            seen |= {j for j in part if j > shared_n}
            if leader(part) != it["meta"]["decoy"]:
                view_bad = True
        if it["meta"].get("evidence") != "shared":
            bad["decoy_not_leading_a_view"] += view_bad
            bad["uncovered_split_criteria"] += len(set(range(shared_n + 1, k["criteria"] + 1)) - seen) > 0
    return bad


def build_hidden_profile(n: int = 500, seed: int = 42, data_dir: Optional[str] = None) -> Dict[str, dict]:
    d = data_dir or DATA_DIR
    hp = load_generator()
    num = hp.generate(n, seed=seed, fmt="numeric")
    txt = hp.generate(n, seed=seed, fmt="text")
    if [x["gold"] for x in num] != [x["gold"] for x in txt]:
        raise RuntimeError("generator formats disagree on gold answers")
    gen_path = hp.__file_path__
    sets = {
        "hp_numeric": [_hp_label(x, "hpnum", "numeric", "split", "") for x in num],
        "hp_numeric_shared": [_hp_label(_twin(x), "hpnum", "numeric", "shared", "_shared") for x in num],
    }
    nl = [_to_nl(x) for x in num]
    for a, b in zip(num, nl):                                      # the prose must carry exactly the same scores
        if parse_nl(b["prompt"]) != parse_numeric(a["prompt"][a["prompt"].index(_ALL_HEAD):]) or \
                [parse_nl(v) for v in b["views"]] != [parse_numeric(v[v.index("Scores you can see:"):]) for v in a["views"]]:
            raise RuntimeError("NL rendering of %s does not round-trip" % a["id"])
    sets["hp_nl"] = [_hp_label(x, "hpnl", "nl", "split", "") for x in nl]
    sets["hp_nl_shared"] = [_hp_label(_twin(x), "hpnl", "nl", "shared", "_shared") for x in nl]
    parsers = {"hp_numeric": parse_numeric, "hp_numeric_shared": parse_numeric, "hp_nl": parse_nl, "hp_nl_shared": parse_nl}
    out = {}
    for name, items in sets.items():
        counts = validate_hidden_profile(items, parsers[name])
        if any(v for k2, v in counts.items() if k2 != "items"):
            raise RuntimeError("%s failed validation: %s" % (name, counts))
        info = {"source": "synthetic: code/%s/hidden_profile.py generate()" % os.path.basename(os.path.dirname(gen_path)), "generator_sha256": file_sha256(gen_path),
                "selection": "first n items of the seeded generator", "seed": seed, "synthetic": True, "validation": counts,
                "knobs": items[0]["meta"]["knobs"], "format": items[0]["meta"]["format"], "evidence": items[0]["meta"]["evidence"]}
        out[name] = register(name, items, info, d)
    return out


# ----------------------------------------------------------------------------- command line
def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m pace_lab.data", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("what", choices=["mmlu_pro", "math500_l45", "hidden_profile", "all"])
    b.add_argument("--refresh", action="store_true", help="re-download the raw pool")
    b.add_argument("--data-dir", default=None)
    sub.add_parser("verify")
    args = ap.parse_args(argv)
    if args.cmd == "verify":
        problems = verify_manifest()
        print("\n".join(problems) if problems else "manifest OK: %s" % ", ".join(sorted(load_manifest()["datasets"])))
        return 1 if problems else 0
    todo = ["mmlu_pro", "math500_l45", "hidden_profile"] if args.what == "all" else [args.what]
    for w in todo:
        if w == "mmlu_pro":
            e = build_mmlu_pro(data_dir=args.data_dir, refresh=args.refresh)
        elif w == "math500_l45":
            e = build_math500_l45(data_dir=args.data_dir, refresh=args.refresh)
        else:
            e = build_hidden_profile(data_dir=args.data_dir)
        print(w, "ok", json.dumps({k: v for k, v in (e.items() if "n" in e else [(kk, vv["n"]) for kk, vv in e.items()]) if k in ("n",) or w == "hidden_profile"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
