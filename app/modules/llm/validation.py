"""JSON Schema validation for LLM output (ТЗ §4.4)."""

from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator


def validate_against_schema(data: Any, schema: dict[str, Any]) -> list[str]:
    """Return a list of human-readable validation errors (empty == valid)."""
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    return [f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors]
