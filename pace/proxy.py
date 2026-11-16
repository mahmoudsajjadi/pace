"""pace proxy: an OpenAI-compatible logging proxy (standard library only).

Point any agent framework's base URL at http://localhost:<port>/v1. Requests are forwarded unchanged to the upstream server and every
call is appended to a JSONL log in the mae_eval trace format (so `mae-eval audit` and `pace report` read it), with latency and cost.

Optional request headers set the labels (they are removed before forwarding):
    X-PACE-System  mas | sas (default mas)      X-PACE-Agent  agent id (default agent)
    X-PACE-Round   integer round (default 0)    X-PACE-Item   item id (default empty, or the first line of --item-file when the caller cannot set headers)
Non-streaming requests only: a request with "stream": true is rejected with HTTP 400 and a clear message (v0.1 limitation).
Prices are never bundled; pass --price-in/--price-out (USD per million tokens) or cost stays null.
"""
from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional

_LABELS = ("x-cme-system", "x-cme-agent", "x-cme-round", "x-cme-item")


def _item_from_file(path: Optional[str]) -> str:
    """Item id for callers that cannot send the X-PACE-Item header (third-party code): the first line of `path`, re-read at every call. Serial runs only."""
    if not path:
        return ""
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.readline().strip()
    except OSError:
        return ""


def make_handler(upstream: str, log_path: str, price_in: Optional[float], price_out: Optional[float], api_key: Optional[str], item_file: Optional[str] = None, default_system: str = "mas"):
    lock = threading.Lock()
    up = upstream.rstrip("/")

    class H(BaseHTTPRequestHandler):
        def _send(self, code: int, payload: bytes, ctype: str = "application/json"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _forward(self, method: str, body: Optional[bytes]):
            headers = {k: v for k, v in self.headers.items() if k.lower() not in _LABELS + ("host", "content-length", "connection")}
            if api_key:
                headers["Authorization"] = "Bearer " + api_key
            req = urllib.request.Request(up + self.path[len("/v1"):] if self.path.startswith("/v1") else up + self.path,
                                         data=body, headers=headers, method=method)
            t0 = time.time()
            try:
                with urllib.request.urlopen(req, timeout=900) as r:
                    return r.status, r.read(), t0, time.time()
            except urllib.error.HTTPError as e:
                return e.code, e.read(), t0, time.time()

        def do_GET(self):
            code, data, _, _ = self._forward("GET", None)
            self._send(code, data)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(n)
            try:
                req = json.loads(raw)
            except json.JSONDecodeError:
                return self._send(400, b'{"error": "invalid JSON"}')
            if req.get("stream"):
                return self._send(400, b'{"error": "pace proxy v0.1 does not support streaming; set stream=false"}')
            code, data, t0, t1 = self._forward("POST", raw)
            if code == 200:
                try:
                    resp = json.loads(data)
                    u = resp.get("usage") or {}
                    det = u.get("completion_tokens_details") or {}
                    pt, ct = u.get("prompt_tokens"), u.get("completion_tokens")
                    cost = None
                    if None not in (price_in, price_out, pt, ct):
                        cost = (pt * price_in + ct * price_out) / 1e6
                    rec = {"system": self.headers.get("X-PACE-System", default_system), "agent_id": self.headers.get("X-PACE-Agent", "agent"),
                           "round": int(self.headers.get("X-PACE-Round", 0)), "item": self.headers.get("X-PACE-Item") or _item_from_file(item_file),
                           "model": resp.get("model", req.get("model")), "prompt_tokens": pt, "completion_tokens": ct,
                           "reasoning_tokens": det.get("reasoning_tokens"), "n_completions": len(resp.get("choices", [])) or 1,
                           "start": t0, "end": t1, "latency": t1 - t0, "cost": cost}
                    if pt is None or ct is None:
                        rec["usage_missing"] = True  # logged, never guessed
                    with lock, open(log_path, "a", encoding="utf-8") as fh:
                        fh.write(json.dumps(rec) + "\n")
                except (ValueError, TypeError):
                    pass
            self._send(code, data)

        def log_message(self, *a):  # quiet
            pass

    return H


def serve(upstream: str, log_path: str, port: int = 8089, host: str = "127.0.0.1", price_in: Optional[float] = None,
          price_out: Optional[float] = None, api_key: Optional[str] = None, item_file: Optional[str] = None, default_system: str = "mas") -> ThreadingHTTPServer:
    srv = ThreadingHTTPServer((host, port), make_handler(upstream, log_path, price_in, price_out, api_key, item_file, default_system))
    return srv
