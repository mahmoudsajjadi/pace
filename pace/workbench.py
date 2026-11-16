"""Local stdlib HTTP workbench and card-v7 file helpers."""

from __future__ import annotations

import csv
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .protocol_v3 import build_evaluation_card_v7, card_v7_to_latex, card_v7_to_markdown


def load_rows(path):
    path = Path(path)
    if path.suffix.lower() == ".jsonl":
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    data = json.loads(path.read_text(encoding="utf-8"))
    return (
        data
        if isinstance(data, list)
        else data.get("rows", data.get("records", [data]))
    )


def card_from_file(path, baseline=None):
    return build_evaluation_card_v7(
        load_rows(path), load_rows(baseline) if baseline else None
    )


def export_html(path):
    source = Path(__file__).with_name("workbench.html")
    Path(path).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


class _Handler(BaseHTTPRequestHandler):
    server_version = "PACEWorkbench/1.0"

    def _json(self, payload, status=200):
        data = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/api/health":
            return self._json({"ok": True, "service": "pace-workbench"})
        if route == "/api/summary":
            root = Path(__file__).resolve().parents[2]
            summary = root / "supplement" / "live_empirical" / "empirical_dynamics.json"
            return self._json(
                json.loads(summary.read_text(encoding="utf-8"))
                if summary.exists()
                else {"status": "unreported"}
            )
        if route == "/":
            data = Path(__file__).with_name("workbench.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self._json({"error": "not found"}, 404)

    def do_POST(self):
        route = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            if route == "/api/evaluate-card-v7":
                return self._json(
                    build_evaluation_card_v7(
                        body.get("rows", []), body.get("baseline_rows")
                    )
                )
            if route == "/api/constructive":
                from .protocol_v3 import evaluate_constructive_objectives

                return self._json(
                    evaluate_constructive_objectives(
                        body.get("comm_rows", []),
                        body.get("placebo_rows", []),
                        body.get("full_base_rows", []),
                        body.get("ver_rows"),
                    )
                )
        except (ValueError, KeyError, TypeError) as exc:
            return self._json({"error": str(exc)}, 400)
        self._json({"error": "not found"}, 404)


def serve(host="127.0.0.1", port=8765, no_browser=False):
    server = ThreadingHTTPServer((host, port), _Handler)
    if not no_browser:
        threading.Timer(0.25, lambda: webbrowser.open(f"http://{host}:{port}/")).start()
    return server


__all__ = [
    "card_from_file",
    "card_v7_to_latex",
    "card_v7_to_markdown",
    "export_html",
    "serve",
]
