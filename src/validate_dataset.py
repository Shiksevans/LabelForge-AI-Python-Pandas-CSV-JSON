"""Validate LabelForge AI annotation CSV and produce a transparent quality report."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import pandas as pd
from schema_config import DEFAULT_ALLOWED, load_schema

ALLOWED = DEFAULT_ALLOWED
REQUIRED_COLUMNS = ["record_id", "text", *ALLOWED.keys()]

def validate_dataframe(
    df: pd.DataFrame,
    allowed: dict[str, set[str]] | None = None,
) -> dict:
    schema = allowed if allowed is not None else ALLOWED
    required_columns = ["record_id", "text", *schema.keys()]
    errors = []
    warnings = []
    missing_columns = [c for c in required_columns if c not in df.columns]
    if missing_columns:
        errors.append({"type": "missing_columns", "columns": missing_columns})
        return {
            "status": "FAIL", "row_count": int(len(df)),
            "missing_columns": missing_columns, "errors": errors, "warnings": warnings
        }

    missing_by_column = {
        col: int(df[col].isna().sum()) for col in required_columns
    }

    # Treat null, empty, and whitespace-only record IDs as missing.
    record_ids = df["record_id"].fillna("").astype(str).str.strip()
    missing_record_id_mask = record_ids.eq("")
    missing_record_id_count = int(missing_record_id_mask.sum())

    # Check duplicate IDs only among nonblank IDs.
    nonblank_record_ids = record_ids[~missing_record_id_mask]
    duplicate_id_count = int(
        nonblank_record_ids.duplicated(keep=False).sum()
    )

    empty_text_count = int(
        df["text"].fillna("").astype(str).str.strip().eq("").sum()
    )

    invalid_labels = {}
    for field, allowed_labels in schema.items():
        raw_values = df[field]
        blank_mask = (
            raw_values.isna()
            | raw_values.astype("string").str.strip().eq("")
        )
        values = set(raw_values[~blank_mask].astype(str).unique())
        invalid = sorted(values - allowed_labels)
        nulls = int(blank_mask.sum())
        if invalid or nulls:
            invalid_labels[field] = {"invalid_values": invalid, "null_count": nulls}
            errors.append({"type": "invalid_labels", "field": field,
                           "invalid_values": invalid, "null_count": nulls})
    if missing_record_id_count:
        errors.append({
            "type": "missing_record_ids",
            "count": missing_record_id_count
        })
    if any(missing_by_column.values()):
        errors.append({"type": "missing_values", "counts": missing_by_column})
    if empty_text_count:
        errors.append({"type": "empty_text", "count": empty_text_count})
    if duplicate_id_count:
        errors.append({"type": "duplicate_ids", "count": duplicate_id_count})
    if len(df) == 0:
        errors.append({"type": "empty_dataset"})

    distributions = {}
    for field in schema:
        counts = df[field].fillna("<MISSING>").astype(str).value_counts().sort_index()
        distributions[field] = {str(k): int(v) for k, v in counts.items()}

    report = {
        "status": "PASS" if not errors else "FAIL",
        "row_count": int(len(df)),
        "unique_record_ids": int(df["record_id"].nunique(dropna=True)),
        "duplicate_id_rows": duplicate_id_count,
        "empty_text_rows": empty_text_count,
        "missing_values_by_column": missing_by_column,
        "invalid_label_details": invalid_labels,
        "label_distributions": distributions,
        "error_count": len(errors),
        "errors": errors,
        "warnings": warnings,
        "note": "Structural validation only; a PASS does not establish semantic label correctness."
    }
    return report

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to annotation CSV")
    parser.add_argument("--report", default="reports/quality_report.json", help="Output JSON report")
    parser.add_argument(
        "--schema",
        help="Optional path to a JSON annotation schema",
    )
    args = parser.parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        return 2
    try:
        df = pd.read_csv(input_path, dtype=str, keep_default_na=True)
    except Exception as exc:
        print(f"ERROR: unable to read CSV: {exc}", file=sys.stderr)
        return 2
    try:
        schema = load_schema(args.schema) if args.schema else ALLOWED
    except (ValueError, OSError) as exc:
        print(f"ERROR: invalid schema: {exc}", file=sys.stderr)
        return 2

    report = validate_dataframe(df, allowed=schema)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
