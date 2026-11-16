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


def load_and_import(path: str, format_name: str) -> list[ItemLog]:
    if format_name == "csv":
        with open(path, newline="", encoding="utf-8") as handle:
            return import_csv(list(csv.DictReader(handle)))
    records = _records(path)
    importer = {
        "autogen": import_autogen,
        "langgraph": import_langgraph,
        "crewai": import_crewai,
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
