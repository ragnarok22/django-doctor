from __future__ import annotations

import json

from django_doctor.core.diagnostics import DoctorResult


def render_json(result: DoctorResult, compact: bool = False) -> str:
    data = result.model_dump(mode="json")
    if compact:
        return json.dumps(data, separators=(",", ":"))
    return json.dumps(data, indent=2)


def render_error(error_type: str, message: str, compact: bool = False) -> str:
    data = {"ok": False, "error": {"type": error_type, "message": message}}
    if compact:
        return json.dumps(data, separators=(",", ":"))
    return json.dumps(data, indent=2)
