"""Validate LabelForge AI annotation CSV and produce a transparent quality report."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import pandas as pd

ALLOWED = {
    "intent": {"billing", "shipping", "technical_support", "account_access", "product_feedback"},
    "sentiment": {"positive", "negative", "neutral", "mixed"},
    "urgency": {"low", "medium", "high"},
    "review_required": {"human_review", "no_review"},
}
REQUIRED_COLUMNS = ["record_id", "text", *ALLOWED.keys()]

def validate_dataframe(df: pd.DataFrame) -> dict:
    errors = []
    warnings = []
    missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_columns:
        errors.append({"type": "missing_columns", "columns": missing_columns})
        return {
            "status": "FAIL", "row_count": int(len(df)),
            "missing_columns": missing_columns, "errors": errors, "warnings": warnings
        }

    missing_by_column = {
        col: int(df[col].isna().sum()) for col in REQUIRED_COLUMNS
    }
    empty_text_count = int(df["text"].fillna("").astype(str).str.strip().eq("").sum())
    duplicate_id_count = int(df["record_id"].duplicated(keep=False).sum())
    invalid_labels = {}
    for field, allowed in ALLOWED.items():
        values = set(df[field].dropna().astype(str).unique())
        invalid = sorted(values - allowed)
        nulls = int(df[field].isna().sum())
        if invalid or nulls:
            invalid_labels[field] = {"invalid_values": invalid, "null_count": nulls}
            errors.append({"type": "invalid_labels", "field": field,
                           "invalid_values": invalid, "null_count": nulls})

    if any(missing_by_column.values()):
        errors.append({"type": "missing_values", "counts": missing_by_column})
    if empty_text_count:
        errors.append({"type": "empty_text", "count": empty_text_count})
    if duplicate_id_count:
        errors.append({"type": "duplicate_ids", "count": duplicate_id_count})
    if len(df) == 0:
        errors.append({"type": "empty_dataset"})

    distributions = {}
    for field in ALLOWED:
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
    report = validate_dataframe(df)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
