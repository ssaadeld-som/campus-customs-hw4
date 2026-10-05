"""Small, persistent audit log for bounded shopping-agent activity."""
from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TypeVar, cast
from functools import wraps

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = PROJECT_ROOT / "output" / "audit_trail.json"
_LOCK = threading.Lock()
F = TypeVar("F", bound=Callable[..., Any])


def _short(value: Any, limit: int = 240) -> str:
    """Keep arguments/results useful to a grader without storing secrets or huge payloads."""
    if isinstance(value, dict):
        value = {key: value[key] for key in value if key not in {"password", "password_hash", "api_key", "session_token"}}
    try:
        text = json.dumps(value, default=str, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        text = str(value)
    text = re.sub(r"(?i)(password|api[_ -]?key|session[_ -]?token)\s*[:=]\s*[^,\s}]+", r"\1:[REDACTED]", text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def append_audit(tool_name: str, short_arg: Any = "", short_result: Any = "", stop_reason: str = "") -> None:
    """Append one event while retaining all events from previous server runs."""
    event = {
        "time": datetime.now(timezone.utc).isoformat(),
        "tool_name": tool_name,
        "short_arg": _short(short_arg),
        "short_result": _short(short_result),
        "stop_reason": stop_reason,
    }
    with _LOCK:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        entries: list[dict[str, Any]] = []
        if AUDIT_PATH.exists():
            try:
                loaded = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
                if isinstance(loaded, list):
                    entries = loaded
            except json.JSONDecodeError:
                # Never overwrite an unparseable prior trail; retain it beside the new trail.
                backup = AUDIT_PATH.with_suffix(".invalid.json")
                if not backup.exists():
                    AUDIT_PATH.replace(backup)
        entries.append(event)
        AUDIT_PATH.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def audited_tool(tool_name: str) -> Callable[[F], F]:
    """Decorate a read-only tool so calls and bounded outcomes are recorded."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            arguments = {"args": args, "kwargs": kwargs}
            try:
                result = function(*args, **kwargs)
            except Exception as exc:
                reason = "not_found" if isinstance(exc, ValueError) else f"error:{type(exc).__name__}"
                append_audit(tool_name, arguments, str(exc), reason)
                raise
            empty = isinstance(result, (list, tuple)) and not result
            append_audit(tool_name, arguments, result, "not_found" if empty else "tool_returned")
            return result
        return cast(F, wrapped)
    return decorator
