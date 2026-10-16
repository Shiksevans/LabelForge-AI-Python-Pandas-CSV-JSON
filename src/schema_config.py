"""Shared annotation schema definitions and configuration loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_ALLOWED: dict[str, set[str]] = {
    "intent": {
        "billing",
        "shipping",
        "technical_support",
        "account_access",
        "product_feedback",
    },
    "sentiment": {"positive", "negative", "neutral", "mixed"},
    "urgency": {"low", "medium", "high"},
    "review_required": {"human_review", "no_review"},
}


def validate_schema(schema: Any) -> dict[str, set[str]]:
    """Validate a schema mapping field names to lists of allowed labels."""
    if not isinstance(schema, dict) or not schema:
        raise ValueError("Schema must be a non-empty JSON object.")

    validated: dict[str, set[str]] = {}

    for field, labels in schema.items():
        if not isinstance(field, str) or not field.strip():
            raise ValueError("Every schema field must have a non-empty name.")

        if field in {"record_id", "text"}:
            raise ValueError(
                f"Schema field '{field}' is reserved for record metadata."
            )

        if not isinstance(labels, list) or not labels:
            raise ValueError(
                f"Labels for '{field}' must be a non-empty list."
            )

        if any(
            not isinstance(label, str) or not label.strip()
            for label in labels
        ):
            raise ValueError(
                f"Labels for '{field}' must be non-empty strings."
            )

        if len(labels) != len(set(labels)):
            raise ValueError(
                f"Labels for '{field}' must not contain duplicates."
            )

        validated[field] = set(labels)

    return validated


def load_schema(path: str | Path) -> dict[str, set[str]]:
    """Load and validate an annotation schema from a JSON file."""
    schema_path = Path(path)

    try:
        with schema_path.open("r", encoding="utf-8") as handle:
            raw_schema = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON schema in '{schema_path}': {exc}"
        ) from exc

    return validate_schema(raw_schema)
