"""Import common multi-agent trace exports into portable PACE JSONL."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .schema import ItemLog, item_log_from_mapping


def _records(path: str) -> list[Any]:
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        value = json.loads(text)
        return value if isinstance(value, list) else [value]
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]


def _usage(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        "prompt_tokens": value.get("prompt_tokens", value.get("input_tokens")),
        "completion_tokens": value.get("completion_tokens", value.get("output_tokens")),
    }


def _message_rows(
    messages: Iterable[Any], item: Any, default_round: int = 0
) -> Iterable[dict[str, Any]]:
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            continue
        row = dict(message)
        usage = _usage(row.get("usage", row.get("token_usage")))
        row.update({key: value for key, value in usage.items() if value is not None})
        row["item"] = row.get("item", row.get("item_id", item))
        row["agent"] = row.get(
            "agent",
            row.get("agent_id", row.get("name", row.get("role", "agent_%d" % index))),
        )
        row["round"] = row.get("round", row.get("round_id", default_round + index))
        if "correct" not in row and "is_correct" not in row:
            continue
        yield row


def import_autogen(records: list[Any]) -> list[ItemLog]:
    result = []
    for record in records:
        if isinstance(record, dict) and isinstance(record.get("messages"), list):
            rows = list(
                _message_rows(
                    record["messages"],
                    record.get("item_id", record.get("id", "item_0")),
                    record.get("round", 0),
                )
            )
            score = record.get("correct", record.get("is_correct"))
            if score is not None:
                for row in rows:
                    row.setdefault("correct", score)
            result.extend(item_log_from_mapping(row) for row in rows)
        elif isinstance(record, dict):
            result.extend(
                item_log_from_mapping(row)
                for row in _message_rows(
                    [record], record.get("item_id", record.get("id", "item_0"))
                )
            )
    return result


def _nested_messages(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if isinstance(value.get("messages"), list):
            yield from (x for x in value["messages"] if isinstance(x, dict))
        else:
            for child in value.values():
                yield from _nested_messages(child)
    elif isinstance(value, list):
        for child in value:
            yield from _nested_messages(child)


def import_langgraph(records: list[Any]) -> list[ItemLog]:
    result = []
    for record in records:
        if not isinstance(record, dict):
            continue
        item = record.get("item_id", record.get("id", "item_0"))
        rows = list(
            _message_rows(
                list(_nested_messages(record.get("state", record))),
                item,
                record.get("round", 0),
            )
        )
        score = record.get("correct", record.get("is_correct"))
        if score is not None:
            for row in rows:
                row.setdefault("correct", score)
        for row in rows:
            result.append(item_log_from_mapping(row))
    return result


def import_crewai(records: list[Any]) -> list[ItemLog]:
    result = []
    for record in records:
        if not isinstance(record, dict):
            continue
        tasks = record.get("tasks", [record])
        for index, task in enumerate(tasks):
            if not isinstance(task, dict):
                continue
            row = dict(task)
            row["item"] = row.get(
                "item",
                row.get("item_id", record.get("item_id", record.get("id", "item_0"))),
            )
            row["agent"] = row.get(
                "agent", row.get("agent_id", row.get("agent_name", "agent_%d" % index))
            )
            row["round"] = row.get("round", row.get("task_index", index))
            row["answer"] = row.get("output", row.get("answer"))
            usage = _usage(row.get("usage", row.get("token_usage", row.get("metrics"))))
            row.update(
                {key: value for key, value in usage.items() if value is not None}
            )
            if row.get("correct") is not None or row.get("is_correct") is not None:
                result.append(item_log_from_mapping(row))
    return result


def import_csv(records: list[Any]) -> list[ItemLog]:
    return [item_log_from_mapping(row) for row in records if isinstance(row, dict)]


def import_inspect(records: list[Any]) -> list[ItemLog]:
    """Convert Inspect AI EvalLog JSON payloads into canonical PACE ItemLog records."""
    result = []
    for record in records:
        if not isinstance(record, dict):
            continue
        samples = record.get("samples", [record])
        for sample in samples:
            if not isinstance(sample, dict):
                continue
            item_id = str(sample.get("id", "item_0"))
            scores = sample.get("scores", {})
            correct = False
            if isinstance(scores, dict):
                for scorer_obj in scores.values():
                    val = scorer_obj.get("value") if isinstance(scorer_obj, dict) else scorer_obj
                    if val in ("C", "correct", 1, 1.0, True):
                        correct = True
                        break
            messages = sample.get("messages", [])
            assistant_turns = [m for m in messages if isinstance(m, dict) and m.get("role") == "assistant"]
            usage = sample.get("model_usage", {})
            total_in = sum(u.get("input_tokens", 0) for u in usage.values() if isinstance(u, dict)) if isinstance(usage, dict) else 0
            total_out = sum(u.get("output_tokens", 0) for u in usage.values() if isinstance(u, dict)) if isinstance(usage, dict) else 0
            total_reason = sum(u.get("reasoning_tokens", 0) for u in usage.values() if isinstance(u, dict)) if isinstance(usage, dict) else 0
            n_turns = max(1, len(assistant_turns))
            for idx, msg in enumerate(assistant_turns or [{}]):
                agent_id = str(msg.get("source") or msg.get("name") or f"agent_{idx}")
                tool_calls = bool(msg.get("tool_calls"))
                result.append(
                    item_log_from_mapping(
                        {
                            "item": item_id,
                            "agent": agent_id,
                            "round": idx + 1,
                            "correct": bool(correct),
                            "prompt_tokens": round(total_in / n_turns, 2) if total_in else None,
                            "completion_tokens": round(total_out / n_turns, 2) if total_out else None,
                            "reasoning_tokens": round(total_reason / n_turns, 2) if total_reason else None,
                            "tool_calls": 1 if tool_calls else 0,
                        }
                    )
                )
    return result


LM_EVAL_METRICS = ("acc", "acc_norm", "exact_match", "pass@1", "em", "accuracy", "correct")


def import_lm_eval(records: list[Any]) -> list[ItemLog]:
    """Convert lm-evaluation-harness `samples_<task>_<time>.jsonl` lines (one scored sample each) into PACE records.

    The sample is one single-agent call (agent `lm_eval`, round 0). Correctness is the first of the accuracy-type metrics named in the line's `metrics` list
    (`acc`, `acc_norm`, `exact_match`, `pass@1`, `em`, ...; value above 0.5), so continuous metrics such as `f1` or `bleu` are not read as correctness and the
    line is skipped. The harness does not store token usage, so token fields stay null (missing, not zero); the first filtered response is kept as `answer`.
    """
    result = []
    for rec in records:
        if not isinstance(rec, dict):
            continue
        doc_id = rec.get("doc_id", rec.get("id"))
        if doc_id is None:
            continue
        names = [str(m).split(",")[0] for m in rec.get("metrics", [])] or list(LM_EVAL_METRICS)
        key = next((k for k in rec if k.split(",")[0] in names and k.split(",")[0] in LM_EVAL_METRICS), None)
        if key is None:
            continue
        value = rec[key]
        if isinstance(value, bool):
            ok = value
        elif isinstance(value, (int, float)):
            ok = float(value) > 0.5
        else:
            continue
        resp = rec.get("filtered_resps", rec.get("resps"))
        while isinstance(resp, list) and resp:
            resp = resp[0]
        task = rec.get("task") or rec.get("task_name")
        result.append(item_log_from_mapping({"item": "%s:%s" % (task, doc_id) if task else doc_id, "agent": "lm_eval", "round": 0, "correct": ok,
                                             "answer": str(resp).strip() if isinstance(resp, (str, int, float)) else None}))
    return result


def load_and_import(path: str, format_name: str) -> list[ItemLog]:
    if format_name == "csv":
        with open(path, newline="", encoding="utf-8") as handle:
            return import_csv(list(csv.DictReader(handle)))
    records = _records(path)
    importer = {
        "autogen": import_autogen,
        "langgraph": import_langgraph,
        "crewai": import_crewai,
        "inspect": import_inspect,
        "lm-eval": import_lm_eval,
    }.get(format_name)
    if importer is None:
        raise ValueError("unknown trace format: %s" % format_name)
    logs = importer(records)
    if not logs:
        raise ValueError("no scored records found in %s trace" % format_name)
    return logs


def write_jsonl(logs: Iterable[ItemLog], output: str) -> int:
    logs = list(logs)
    if not logs:
        raise ValueError("no records to write")
    with open(output, "w", encoding="utf-8", newline="\n") as handle:
        handle.writelines(
            json.dumps(log.to_dict(), sort_keys=True) + "\n" for log in logs
        )
    return len(logs)
