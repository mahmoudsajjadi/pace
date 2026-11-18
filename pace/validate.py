"""`pace validate-log`: structural checks of a PACE JSONL trace before a card is computed from it.

Two kinds of file are accepted and detected from the first record:
  * per-call records written by ``Session.write_jsonl(path, calls=True)`` (schema: ``pace.sdk.FIELDS``);
  * PACE rows written by ``Session.write_jsonl(path)`` or an importer (item, agent, round, correct, optional token and latency fields).

Checks (each issue has a severity, a code, the line, a message and a fix):
  schema            parse errors, missing required fields, wrong types, negative numbers, unknown usage_status, ended_at before started_at;
  duplicate_call_id the same call_id twice (a retry or double callback counted twice), and duplicate provider_response_id;
  dag               a parent_call_id that names no call, a call that is its own parent, or a cycle in the parent graph;
  usage_sentinel    zero tokens used where usage was not reported (``None`` means not measured, 0 means measured as zero), usage_status that contradicts the token fields.

Exit codes of the CLI: 0 clean (warnings allowed unless --strict), 1 at least one error (or a warning with --strict), 2 the file cannot be read or is empty.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .sdk import FIELDS

TOKEN_FIELDS = ("input_tokens", "output_tokens", "reasoning_tokens", "cache_read_tokens", "cache_write_tokens")
CALL_REQUIRED = ("call_id", "task_id", "agent_id", "usage_status", "status")
ROW_REQUIRED = ("item", "agent", "round", "correct")
ROW_NUMERIC = ("prompt_tokens", "completion_tokens", "reasoning_tokens", "latency_s", "cost_usd")
USAGE_STATUS = ("reported", "partial", "missing")


def _num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and not (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))


class _Report:
    def __init__(self) -> None:
        self.issues: list[dict[str, Any]] = []

    def add(self, severity: str, code: str, line: int | None, message: str, fix: str, call_id: str | None = None) -> None:
        self.issues.append({"severity": severity, "code": code, "line": line, "call_id": call_id, "message": message, "fix": fix})


def read_records(path: str) -> tuple[list[tuple[int, dict[str, Any]]], _Report]:
    rep = _Report()
    recs: list[tuple[int, dict[str, Any]]] = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            rep.add("error", "schema", n, "line is not valid JSON (%s)" % e.msg, "write one JSON object per line (Session.write_jsonl does)")
            continue
        if not isinstance(obj, dict):
            rep.add("error", "schema", n, "record is %s, not a JSON object" % type(obj).__name__, "write one JSON object per line")
            continue
        recs.append((n, obj))
    return recs, rep


def detect_kind(recs: list[tuple[int, dict[str, Any]]]) -> str:
    first = recs[0][1]
    return "calls" if ("call_id" in first or "task_id" in first) else "rows"


def _check_call(n: int, r: dict[str, Any], rep: _Report) -> None:
    cid = r.get("call_id")
    cid_s = None if cid is None else str(cid)
    for k in CALL_REQUIRED:
        if r.get(k) is None:
            rep.add("error", "schema", n, "required field %s is missing or null" % k, "set %s on every call record" % k, cid_s)
    missing_keys = [k for k in FIELDS if k not in r]
    if missing_keys:
        rep.add("warning", "schema", n, "fields absent from the record: %s" % ", ".join(missing_keys[:6]) + (" ..." if len(missing_keys) > 6 else ""), "write records with Session.write_jsonl(path, calls=True) so every field is present", cid_s)
    for k in TOKEN_FIELDS:
        v = r.get(k)
        if v is not None and (not _num(v) or v < 0):
            rep.add("error", "schema", n, "%s = %r is not a non-negative number or null" % (k, v), "use null for tokens the provider did not report", cid_s)
    el = r.get("elapsed_seconds")
    if el is not None and (not _num(el) or el < 0):
        rep.add("error", "schema", n, "elapsed_seconds = %r is not a non-negative number or null" % (el,), "record the call duration in seconds", cid_s)
    s, e = r.get("started_at"), r.get("ended_at")
    if _num(s) and _num(e) and e < s:
        rep.add("error", "schema", n, "ended_at (%s) is before started_at (%s)" % (e, s), "check the clock source of the adapter", cid_s)
    st = r.get("usage_status")
    if st is not None and st not in USAGE_STATUS:
        rep.add("error", "schema", n, "usage_status = %r, expected one of %s" % (st, "/".join(USAGE_STATUS)), "let the Session compute usage_status", cid_s)
    have_in, have_out = r.get("input_tokens") is not None, r.get("output_tokens") is not None
    expect = "reported" if (have_in and have_out) else ("partial" if (have_in or have_out) else "missing")
    if st in USAGE_STATUS and st != expect:
        rep.add("error", "usage_sentinel", n, "usage_status is %r but the token fields imply %r" % (st, expect), "recompute usage_status from input_tokens and output_tokens", cid_s)
    raw = r.get("raw_usage")
    if st == "missing" or (not have_in and not have_out):
        zeros = [k for k in TOKEN_FIELDS if _num(r.get(k)) and r.get(k) == 0]
        if zeros:
            rep.add("error", "usage_sentinel", n, "%s is 0 although usage was not reported: 0 means measured as zero, null means not measured" % ", ".join(zeros), "write null, never 0, for unreported usage", cid_s)
    if _num(r.get("input_tokens")) and _num(r.get("output_tokens")) and r["input_tokens"] == 0 and r["output_tokens"] == 0 and raw in (None, {}, [], ""):
        rep.add("error", "usage_sentinel", n, "input and output tokens are both 0 with no raw_usage: this looks like a placeholder for missing usage", "write null, or keep the provider's raw_usage that shows the zeros", cid_s)
    if raw not in (None, {}, [], "") and not have_in and not have_out:
        rep.add("warning", "usage_sentinel", n, "raw_usage is present but no token field was parsed from it", "pass the provider usage dict through normalize_usage or set the token fields", cid_s)


def _check_row(n: int, r: dict[str, Any], rep: _Report) -> None:
    for k in ROW_REQUIRED:
        if k not in r or r[k] is None:
            rep.add("error", "schema", n, "required field %s is missing or null" % k, "PACE rows need item, agent, round and correct")
    if "round" in r and r["round"] is not None and (not isinstance(r["round"], int) or isinstance(r["round"], bool) or r["round"] < 0):
        rep.add("error", "schema", n, "round = %r is not a non-negative integer" % (r["round"],), "use the round index of the call")
    if "correct" in r and r["correct"] is not None and not isinstance(r["correct"], (bool, int, float)):
        rep.add("error", "schema", n, "correct = %r is not boolean or numeric" % (r["correct"],), "use true/false or a 0..1 credit")
    for k in ROW_NUMERIC:
        v = r.get(k)
        if v is not None and (not _num(v) or v < 0):
            rep.add("error", "schema", n, "%s = %r is not a non-negative number" % (k, v), "omit the field when it was not measured")
    if r.get("prompt_tokens") == 0 and r.get("completion_tokens") == 0:
        rep.add("warning", "usage_sentinel", n, "prompt_tokens and completion_tokens are both 0: if the provider did not report usage, omit the fields instead of writing 0", "omit unmeasured token fields (a row without them is counted as not measured)")


def _check_dag(calls: list[tuple[int, dict[str, Any]]], rep: _Report) -> None:
    ids: dict[str, int] = {}
    rids: dict[str, int] = {}
    for n, r in calls:
        cid, rid = r.get("call_id"), r.get("provider_response_id")
        if cid is not None:
            if str(cid) in ids:
                rep.add("error", "duplicate_call_id", n, "call_id %r repeats line %d" % (cid, ids[str(cid)]), "give every call a unique call_id; drop retries or double callbacks", str(cid))
            else:
                ids[str(cid)] = n
        if rid is not None:
            if str(rid) in rids:
                rep.add("error", "duplicate_call_id", n, "provider_response_id %r repeats line %d (the same response counted twice)" % (rid, rids[str(rid)]), "keep one record per provider response", None if cid is None else str(cid))
            else:
                rids[str(rid)] = n
    parent = {}
    for n, r in calls:
        cid, pid = r.get("call_id"), r.get("parent_call_id")
        if cid is None or pid is None:
            continue
        cid, pid = str(cid), str(pid)
        if pid == cid:
            rep.add("error", "dag", n, "call %r is its own parent" % cid, "set parent_call_id to the call that caused this one, or null", cid)
        elif pid not in ids:
            rep.add("error", "dag", n, "parent_call_id %r names no call in the file" % pid, "include the parent call or set parent_call_id to null", cid)
        else:
            parent.setdefault(cid, pid)
    state: dict[str, int] = {}
    reported: set[str] = set()
    for start in parent:
        path, cur = [], start
        while cur in parent and state.get(cur) is None:
            state[cur] = 1
            path.append(cur)
            cur = parent[cur]
        if state.get(cur) == 1 and cur in path:
            cyc = path[path.index(cur):]
            key = min(cyc)
            if key not in reported:
                reported.add(key)
                rep.add("error", "dag", ids.get(cyc[0]), "parent_call_id cycle: %s" % " -> ".join(cyc + [cyc[0]]), "break the cycle: a call cannot be its own ancestor", cyc[0])
        for c in path:
            state[c] = 2


def validate(path: str) -> dict[str, Any]:
    """Validate one JSONL file and return the report dict (same content as --json)."""
    try:
        recs, rep = read_records(path)
    except (OSError, UnicodeDecodeError) as e:
        return {"path": path, "ok": False, "exit_code": 2, "kind": None, "n_records": 0, "n_errors": 1, "n_warnings": 0, "issues": [
            {"severity": "error", "code": "unreadable", "line": None, "call_id": None, "message": "cannot read the file: %s" % e, "fix": "check the path and the encoding (UTF-8)"}], "summary": {}}
    if not recs:
        if not rep.issues:
            rep.add("error", "empty", None, "the file has no records", "write at least one call with Session.write_jsonl")
        return _finish(path, rep, None, 0, {}, 2 if not rep.issues or rep.issues[0]["code"] == "empty" else 1)
    kind = detect_kind(recs)
    for n, r in recs:
        (_check_call if kind == "calls" else _check_row)(n, r, rep)
    summary: dict[str, Any] = {}
    if kind == "calls":
        _check_dag(recs, rep)
        summary = {"usage_reported": sum(1 for _, r in recs if r.get("usage_status") == "reported"), "usage_partial": sum(1 for _, r in recs if r.get("usage_status") == "partial"),
                   "usage_missing": sum(1 for _, r in recs if r.get("usage_status") == "missing"), "n_tasks": len({str(r.get("task_id")) for _, r in recs}),
                   "n_with_parent": sum(1 for _, r in recs if r.get("parent_call_id") is not None)}
    else:
        summary = {"n_items": len({str(r.get("item")) for _, r in recs}), "n_with_tokens": sum(1 for _, r in recs if r.get("prompt_tokens") is not None and r.get("completion_tokens") is not None)}
    return _finish(path, rep, kind, len(recs), summary, None)


def _finish(path: str, rep: _Report, kind: str | None, n: int, summary: dict[str, Any], forced_exit: int | None) -> dict[str, Any]:
    errs = sum(1 for i in rep.issues if i["severity"] == "error")
    warns = sum(1 for i in rep.issues if i["severity"] == "warning")
    code = forced_exit if forced_exit is not None else (1 if errs else 0)
    return {"path": path, "ok": errs == 0, "exit_code": code, "kind": kind, "n_records": n, "n_errors": errs, "n_warnings": warns, "issues": rep.issues, "summary": summary}


def render_text(rep: dict[str, Any], limit: int = 25) -> str:
    out = ["%s: %s records (%s), %d error(s), %d warning(s)" % (rep["path"], rep["n_records"], rep["kind"] or "unknown", rep["n_errors"], rep["n_warnings"])]
    for i in rep["issues"][:limit]:
        where = ("line %d" % i["line"]) if i["line"] else "file"
        out.append("  %-7s %-17s %s: %s\n          fix: %s" % (i["severity"], i["code"], where, i["message"], i["fix"]))
    if len(rep["issues"]) > limit:
        out.append("  ... %d more (use --report to write all of them)" % (len(rep["issues"]) - limit))
    out.append("OK" if rep["ok"] else "FAILED")
    return "\n".join(out) + "\n"
