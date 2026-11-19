"""`pace doctor`: a self-check of the installation (Python, pace version, dependencies, the card schema, the framework adapters).

Core requirements (a failure exits with 1): Python >= 3.10, the pace modules import, numpy is installed, and the built-in PACE Card v2 schema is well formed. Everything else is a warning
(optional dependency missing, schema file of the repository differing from the built-in schema, an adapter file absent, an adapter that does not import): the exit code stays 0 and the
report says what is missing. Adapters are checked for their own source (examples/adapters/<name>_adapter.py, present in a repository or source checkout, not in a wheel) and whether it
imports without its SDK; whether the framework SDK itself is installed is informational only.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any, Callable

EXPECTED_MIN_PYTHON = (3, 10)
DEPENDENCIES = (("numpy", True, "core"), ("matplotlib", False, "figures (pip install pace-eval[plot])"), ("scipy", False, "analysis scripts"), ("pandas", False, "analysis scripts"))
ADAPTERS = (("google_adk", "google.adk"), ("langgraph", "langgraph"), ("crewai", "crewai"), ("autogen", "autogen_agentchat"), ("openai_agents", "agents"))


def get_version(name: str) -> str | None:
    """Installed version of a distribution or importable module, None when it is not installed."""
    try:
        from importlib import metadata
        return metadata.version(name)
    except Exception:                                                                             # noqa: BLE001 (PackageNotFoundError and broken metadata)
        pass
    try:
        mod = importlib.import_module(name)
        return str(getattr(mod, "__version__", "unknown"))
    except Exception:                                                                             # noqa: BLE001
        return None


def has_module(dotted: str) -> bool:
    try:
        return importlib.util.find_spec(dotted) is not None
    except (ImportError, ValueError, AttributeError):
        return False


def _search_roots() -> list[Path]:
    here = Path(__file__).resolve().parent
    return [here.parent.parent, here.parent, here.parent.parent.parent]


def find_file(*parts: str) -> Path | None:
    for root in _search_roots():
        p = root.joinpath(*parts)
        if p.is_file():
            return p
    return None


def check_schema() -> dict[str, Any]:
    from .card import CARD_V2_SCHEMA

    out: dict[str, Any] = {"builtin": False, "file": None, "file_in_sync": None, "note": ""}
    try:
        ok = (CARD_V2_SCHEMA.get("title") == "PACE Evaluation Card" and set(CARD_V2_SCHEMA["required"]) >= {"schema", "A_identity", "B_resource_accounting", "C_baseline_specification",
                                                                                                               "D_statistical_evidence", "E_reproducibility"})
    except (KeyError, AttributeError, TypeError):
        ok = False
    out["builtin"] = ok
    f = find_file("docs", "pace_card_v2.schema.json")
    if f is None:
        out["note"] = "docs/pace_card_v2.schema.json is not shipped with this installation; the built-in schema (pace.card.CARD_V2_SCHEMA) is used"
        return out
    out["file"] = str(f)
    try:
        out["file_in_sync"] = json.loads(f.read_text(encoding="utf-8")) == json.loads(json.dumps(CARD_V2_SCHEMA))
    except (OSError, ValueError):
        out["file_in_sync"] = False
    if out["file_in_sync"] is False:
        out["note"] = "the schema file differs from the built-in schema"
    return out


def check_adapters(has: Callable[[str], bool] = has_module) -> list[dict[str, Any]]:
    out = []
    for name, sdk in ADAPTERS:
        f = find_file("examples", "adapters", name + "_adapter.py")
        rec = {"name": name, "source": str(f) if f else None, "imports_without_sdk": None, "sdk_module": sdk, "sdk_installed": bool(has(sdk)), "ready": False, "note": ""}
        if f is None:
            rec["note"] = "adapter source not found (examples/adapters is part of the repository, not of the wheel)"
        else:
            try:
                spec = importlib.util.spec_from_file_location("pace_doctor_" + name, f)
                mod = importlib.util.module_from_spec(spec)
                sys.path.insert(0, str(f.parent))
                try:
                    spec.loader.exec_module(mod)                                                      # type: ignore[union-attr]
                finally:
                    sys.path.remove(str(f.parent))
                rec["imports_without_sdk"] = True
                rec["ready"] = True
            except Exception as e:                                                                    # noqa: BLE001
                rec["imports_without_sdk"] = False
                rec["note"] = "import failed: %s: %s" % (type(e).__name__, e)
        out.append(rec)
    return out


def collect(version_of: Callable[[str], str | None] = get_version, has: Callable[[str], bool] = has_module) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    py_ok = sys.version_info[:2] >= EXPECTED_MIN_PYTHON
    if not py_ok:
        errors.append("Python %d.%d or later is required (found %s)" % (EXPECTED_MIN_PYTHON + (platform.python_version(),)))
    try:
        import pace
        from . import sdk as _sdk  # noqa: F401
        from . import card as _card  # noqa: F401
        from . import compare as _compare  # noqa: F401
        from . import validate as _validate  # noqa: F401
        pace_version = str(pace.__version__)
        import_ok = True
    except Exception as e:                                                                          # noqa: BLE001
        pace_version, import_ok = None, False
        errors.append("pace does not import: %s: %s" % (type(e).__name__, e))
    dist = version_of("pace-eval")
    if import_ok and dist is not None and dist != pace_version:
        warnings.append("the installed distribution pace-eval %s differs from pace.__version__ %s (a stale install next to the source tree?)" % (dist, pace_version))
    deps = []
    for name, required, why in DEPENDENCIES:
        v = version_of(name)
        deps.append({"name": name, "required": required, "installed": v is not None, "version": v, "purpose": why})
        if v is None:
            (errors if required else warnings).append("%s is not installed (%s)" % (name, why))
    schema = check_schema()
    if not schema["builtin"]:
        errors.append("the built-in PACE Card v2 schema is missing or malformed")
    if schema["file_in_sync"] is False:
        warnings.append(schema["note"])
    adapters = check_adapters(has)
    for a in adapters:
        if not a["ready"]:
            warnings.append("adapter %s: %s" % (a["name"], a["note"]))
    return {"schema": "pace-doctor/v1", "ok": not errors, "pace_version": pace_version, "distribution_version": dist,
            "python": {"version": platform.python_version(), "executable": sys.executable, "ok": py_ok, "minimum": "%d.%d" % EXPECTED_MIN_PYTHON},
            "dependencies": deps, "card_schema": schema, "adapters": adapters, "errors": errors, "warnings": warnings}


def render_text(rep: dict[str, Any]) -> str:
    mark = lambda ok: "ok     " if ok else "MISSING"  # noqa: E731
    L = ["PACE doctor", "  pace %s (distribution %s)" % (rep["pace_version"] or "n/a", rep["distribution_version"] or "not installed as a distribution"),
         "  [%s] Python %s (needs %s or later) at %s" % (mark(rep["python"]["ok"]), rep["python"]["version"], rep["python"]["minimum"], rep["python"]["executable"]), "  dependencies:"]
    for d in rep["dependencies"]:
        L.append("    [%s] %-10s %-10s %s%s" % ("ok     " if d["installed"] else ("MISSING" if d["required"] else "absent "), d["name"], d["version"] or "-", "required: " if d["required"] else "optional: ", d["purpose"]))
    s = rep["card_schema"]
    L.append("  card schema: built-in %s; file %s%s" % ("ok" if s["builtin"] else "MISSING", s["file"] or "not shipped", "" if s["file_in_sync"] is None else (" (in sync)" if s["file_in_sync"] else " (DIFFERS)")))
    L.append("  adapters:")
    for a in rep["adapters"]:
        L.append("    [%s] %-14s imports without SDK: %-5s SDK %s installed%s" % ("ready  " if a["ready"] else "n/a    ", a["name"], {True: "yes", False: "NO", None: "n/a"}[a["imports_without_sdk"]],
                                                                                 "is" if a["sdk_installed"] else "not", ("  -- " + a["note"]) if a["note"] else ""))
    for w in rep["warnings"]:
        L.append("  warning: " + w)
    for e in rep["errors"]:
        L.append("  ERROR: " + e)
    L.append("RESULT: " + ("OK" if rep["ok"] else "FAILED") + (" (%d warning(s))" % len(rep["warnings"]) if rep["warnings"] else ""))
    return "\n".join(L) + "\n"
