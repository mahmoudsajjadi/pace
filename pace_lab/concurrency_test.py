"""Local HTTP harness for testing pace_lab client concurrency and retry accounting."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .clients import LLMClient, LLMRequest


class MockOpenAIHandler(BaseHTTPRequestHandler):
    latency_per_token = 0.0
    response_tokens = 8
    failures_remaining = 0
    failure_status = 429

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        if type(self).failures_remaining:
            type(self).failures_remaining -= 1
            self.send_response(type(self).failure_status)
            self.end_headers()
            return
        time.sleep(type(self).latency_per_token * type(self).response_tokens)
        payload = {
            "choices": [{"message": {"content": "Answer: A"}, "finish_reason": "stop"}],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": type(self).response_tokens,
            },
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


class LocalMockServer:
    """Context manager for an ephemeral threaded OpenAI-compatible endpoint."""

    def __init__(
        self,
        latency_per_token: float = 0.0,
        response_tokens: int = 8,
        failures: int = 0,
        failure_status: int = 429,
    ):
        self.settings = (latency_per_token, response_tokens, failures, failure_status)
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None

    def __enter__(self) -> LocalMockServer:
        latency, tokens, failures, status = self.settings
        MockOpenAIHandler.latency_per_token, MockOpenAIHandler.response_tokens = (
            latency,
            tokens,
        )
        MockOpenAIHandler.failures_remaining, MockOpenAIHandler.failure_status = (
            failures,
            status,
        )
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MockOpenAIHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    @property
    def url(self) -> str:
        if self.server is None:
            raise RuntimeError("server is not running")
        return "http://127.0.0.1:%d/v1" % self.server.server_port

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=2)
        return False


def run_concurrency_test(
    workers: int = 1, requests: int = 8, latency_per_token: float = 0.001
) -> dict:
    """Run local threaded calls and return throughput/timing accounting."""
    if workers < 1 or requests < 1:
        raise ValueError("workers and requests must be positive")
    with LocalMockServer(latency_per_token=latency_per_token) as server:
        client = LLMClient(
            ".", transport=None, groq_url=server.url, max_retries=0, timeout=5
        )
        # The real transport is intentionally used only against this local endpoint.
        import concurrent.futures

        start = time.perf_counter()

        def call(index: int):
            return client.call(
                LLMRequest(
                    "groq", "mock", "Answer A", max_tokens=16, item_id=str(index)
                )
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(call, range(requests)))
        elapsed = time.perf_counter() - start
    return {
        "workers": workers,
        "requests": requests,
        "elapsed_s": elapsed,
        "ok": sum(result.ok for result in results),
        "prompt_tokens": sum(
            result.record.get("prompt_tokens") or 0 for result in results
        ),
        "completion_tokens": sum(
            result.record.get("completion_tokens") or 0 for result in results
        ),
    }
