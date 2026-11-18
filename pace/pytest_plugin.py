"""pytest plugin (entry point `pytest11`): audit the model calls of a test with `@pytest.mark.pace_audit`.

    import pytest

    @pytest.mark.pace_audit(require_usage=True, max_tokens=50_000, max_calls=40)
    def test_debate_budget(pace_session):
        run_my_agents(pace_session)            # record calls with pace_session.call(...) / .record(...)

The `pace_session` fixture is a `pace.Session`. After the test body passes, a marked test is audited (`Session.audit`): duplicate call records, missing token usage (when
`require_usage=True`), token or call ceilings and failed calls turn the test into a failure with the reasons listed. `--pace-audit-dir DIR` also writes the PACE rows
(`<test>.pace.jsonl`) and the single-trace card (`<test>.card.json`) of every audited test. Unmarked tests are never changed. Import-safe: nothing heavy is imported at load.
"""
from __future__ import annotations

import json
import os
import re

import pytest


def pytest_addoption(parser):
    parser.addoption("--pace-audit-dir", action="store", default=None, help="write PACE rows and the card of every @pytest.mark.pace_audit test to this directory")


def pytest_configure(config):
    config.addinivalue_line("markers", "pace_audit(require_usage=False, max_tokens=None, max_calls=None): audit the calls of the test's pace_session after it passes")


@pytest.fixture
def pace_session(request):
    from .sdk import Session

    session = Session(session_id=re.sub(r"\W+", "_", request.node.nodeid)[:60])
    request.node._pace_session = session
    return session


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    marker = item.get_closest_marker("pace_audit")
    session = getattr(item, "_pace_session", None)
    if marker is None or session is None or call.when != "call":
        return
    outdir = item.config.getoption("--pace-audit-dir")
    if outdir:
        os.makedirs(outdir, exist_ok=True)
        stem = re.sub(r"\W+", "_", item.nodeid)[:100]
        session.write_jsonl(os.path.join(outdir, stem + ".pace.jsonl"))
        try:
            card = session.card()
        except ValueError:
            card = {"note": "no scored calls: call session.mark(...) to score tasks"}
        with open(os.path.join(outdir, stem + ".card.json"), "w", encoding="utf-8") as fh:
            json.dump(card, fh, indent=2, default=str)
    if rep.passed:
        problems = session.audit(**{k: v for k, v in marker.kwargs.items() if k in ("require_usage", "max_tokens", "max_calls")})
        if problems:
            rep.outcome = "failed"
            rep.longrepr = "pace_audit failed:\n  - " + "\n  - ".join(problems)
