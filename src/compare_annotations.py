"""Compare two independent LabelForge AI annotation files.

Uses only the unlabeled source batch plus two separately completed annotation CSVs.
It deliberately does not use annotation_dataset.csv as a second annotator.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ALLOWED = {
    "intent": {"billing", "shipping", "technical_support", "account_access", "product_feedback"},
    "sentiment": {"positive", "negative", "neutral", "mixed"},
    "urgency": {"low", "medium", "high"},
    "review_required": {"human_review", "no_review"},
}
LABEL_FIELDS = list(ALLOWED)
SOURCE_COLUMNS = ["record_id", "text"]
ANNOTATION_COLUMNS = ["record_id", "text", *LABEL_FIELDS]


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Read UTF-8 CSV, preserving strings and returning header names."""
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = list(reader.fieldnames or [])
        rows = []
        for row in reader:
            rows.append({key: (value if value is not None else "") for key, value in row.items() if key is not None})
    return rows, headers


def write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def blank(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def index_rows(rows: list[dict[str, str]], label: str, issues: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    duplicate_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        record_id = row.get("record_id", "").strip()
        if not record_id:
            issues.append({"file": label, "record_id": "", "row": row_number, "issue": "missing_record_id", "detail": "Row has no record_id."})
            continue
        if record_id in indexed:
            duplicate_ids.add(record_id)
            issues.append({"file": label, "record_id": record_id, "row": row_number, "issue": "duplicate_record_id", "detail": "Record ID occurs more than once; this ID is excluded from comparison."})
            continue
        indexed[record_id] = {key: value.strip() for key, value in row.items()}
    for duplicate in duplicate_ids:
        indexed.pop(duplicate, None)
    return indexed


def cohen_kappa(a_values: list[str], b_values: list[str], labels: set[str]) -> float | None:
    """Return Cohen's kappa, or None when it is undefined."""
    n = len(a_values)
    if n == 0 or n != len(b_values):
        return None
    observed = sum(a == b for a, b in zip(a_values, b_values)) / n
    counts_a = Counter(a_values)
    counts_b = Counter(b_values)
    expected = sum((counts_a[label] / n) * (counts_b[label] / n) for label in labels)
    if math.isclose(1.0 - expected, 0.0, abs_tol=1e-12):
        return None
    return (observed - expected) / (1.0 - expected)


def safe_pct(numerator: int, denominator: int) -> float | None:
    return (100.0 * numerator / denominator) if denominator else None


def fmt_pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.1f}%"


def fmt_kappa(value: float | None) -> str:
    return "undefined (insufficient variation or no paired labels)" if value is None else f"{value:.3f}"


def compare(source_path: Path, annotator_a_path: Path, annotator_b_path: Path, output_dir: Path) -> dict[str, Any]:
    if not source_path.exists():
        raise FileNotFoundError(f"Source batch not found: {source_path}")
    if not annotator_a_path.exists():
        raise FileNotFoundError(f"Annotator A file not found: {annotator_a_path}")
    if not annotator_b_path.exists():
        raise FileNotFoundError(f"Annotator B file not found: {annotator_b_path}")

    source_rows, source_headers = read_csv(source_path)
    a_rows, a_headers = read_csv(annotator_a_path)
    b_rows, b_headers = read_csv(annotator_b_path)
    issues: list[dict[str, Any]] = []

    for label, headers, expected in [
        ("source", source_headers, SOURCE_COLUMNS),
        ("annotator_a", a_headers, ANNOTATION_COLUMNS),
        ("annotator_b", b_headers, ANNOTATION_COLUMNS),
    ]:
        missing = [column for column in expected if column not in headers]
        if missing:
            issues.append({"file": label, "record_id": "", "row": "", "issue": "missing_columns", "detail": f"Missing required columns: {', '.join(missing)}"})

    if any(i["issue"] == "missing_columns" for i in issues):
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "validation_report.json").write_text(json.dumps({"status": "FAIL", "issues": issues}, indent=2), encoding="utf-8")
        raise ValueError("One or more input files are missing required columns. See validation_report.json.")

    source_index = index_rows(source_rows, "source", issues)
    a_index = index_rows(a_rows, "annotator_a", issues)
    b_index = index_rows(b_rows, "annotator_b", issues)
    source_ids = set(source_index)

    # Validate annotation record IDs and ensure annotators did not accidentally edit source text.
    for label, indexed in [("annotator_a", a_index), ("annotator_b", b_index)]:
        for record_id in sorted(set(indexed) - source_ids):
            issues.append({"file": label, "record_id": record_id, "row": "", "issue": "unexpected_record_id", "detail": "Record ID is not present in the source batch."})
        for record_id in sorted(set(indexed) & source_ids):
            if indexed[record_id].get("text", "").strip() != source_index[record_id].get("text", "").strip():
                issues.append({"file": label, "record_id": record_id, "row": "", "issue": "text_mismatch", "detail": "Text differs from source; this record is excluded from comparisons for this annotator."})

    def row_text_matches(record_id: str, indexed: dict[str, dict[str, str]]) -> bool:
        return record_id in indexed and indexed[record_id].get("text", "").strip() == source_index[record_id].get("text", "").strip()

    invalid_by_annotator: dict[str, dict[str, int]] = {"annotator_a": defaultdict(int), "annotator_b": defaultdict(int)}
    missing_by_annotator: dict[str, dict[str, int]] = {"annotator_a": defaultdict(int), "annotator_b": defaultdict(int)}
    valid_cells: dict[str, dict[str, set[str]]] = {"annotator_a": defaultdict(set), "annotator_b": defaultdict(set)}

    for label, indexed in [("annotator_a", a_index), ("annotator_b", b_index)]:
        for record_id in source_ids:
            if not row_text_matches(record_id, indexed):
                missing_by_annotator[label]["records_missing_or_text_mismatched"] += 1
                continue
            for field in LABEL_FIELDS:
                value = indexed[record_id].get(field, "").strip()
                if blank(value):
                    missing_by_annotator[label][field] += 1
                    issues.append({"file": label, "record_id": record_id, "row": "", "issue": "missing_label", "detail": f"No label supplied for field '{field}'."})
                elif value not in ALLOWED[field]:
                    invalid_by_annotator[label][field] += 1
                    issues.append({"file": label, "record_id": record_id, "row": "", "issue": "invalid_label", "detail": f"'{value}' is not an allowed label for '{field}'."})
                else:
                    valid_cells[label][field].add(record_id)

    field_metrics: list[dict[str, Any]] = []
    disagreement_rows: list[dict[str, Any]] = []
    confusion_rows: list[dict[str, Any]] = []
    overall_full_match = 0
    complete_pair_ids = []
    all_field_values: dict[str, tuple[list[str], list[str]]] = {}

    for record_id in sorted(source_ids):
        if not row_text_matches(record_id, a_index) or not row_text_matches(record_id, b_index):
            continue
        if all(a_index[record_id].get(field, "") in ALLOWED[field] and b_index[record_id].get(field, "") in ALLOWED[field] for field in LABEL_FIELDS):
            complete_pair_ids.append(record_id)
            if all(a_index[record_id][field] == b_index[record_id][field] for field in LABEL_FIELDS):
                overall_full_match += 1

    for field in LABEL_FIELDS:
        comparable_ids = sorted(valid_cells["annotator_a"][field] & valid_cells["annotator_b"][field] & source_ids)
        a_values = [a_index[record_id][field] for record_id in comparable_ids]
        b_values = [b_index[record_id][field] for record_id in comparable_ids]
        matches = sum(a == b for a, b in zip(a_values, b_values))
        disagreements = len(comparable_ids) - matches
        kappa = cohen_kappa(a_values, b_values, ALLOWED[field])
        metric = {
            "field": field,
            "source_rows": len(source_rows),
            "paired_valid_n": len(comparable_ids),
            "matching_n": matches,
            "disagreement_n": disagreements,
            "percent_agreement": round(safe_pct(matches, len(comparable_ids)), 3) if comparable_ids else None,
            "cohens_kappa": round(kappa, 6) if kappa is not None else None,
            "interpretation_note": "Kappa is undefined when expected agreement is 1.0 or there are no paired valid labels." if kappa is None else "Interpret kappa in context; small or imbalanced samples can make it unstable.",
        }
        field_metrics.append(metric)
        all_field_values[field] = (a_values, b_values)

        joint_labels = sorted(ALLOWED[field])
        cross = Counter(zip(a_values, b_values))
        for a_label in joint_labels:
            for b_label in joint_labels:
                count = cross.get((a_label, b_label), 0)
                if count:
                    confusion_rows.append({"field": field, "annotator_a_label": a_label, "annotator_b_label": b_label, "count": count})

        for record_id in comparable_ids:
            a_label, b_label = a_index[record_id][field], b_index[record_id][field]
            if a_label != b_label:
                disagreement_rows.append({
                    "record_id": record_id,
                    "text": source_index[record_id].get("text", ""),
                    "field": field,
                    "annotator_a_label": a_label,
                    "annotator_b_label": b_label,
                    "issue": "label_disagreement",
                    "adjudication_status": "pending",
                    "adjudicated_label": "",
                    "adjudication_rationale": "",
                })

    expected_ids = source_ids
    def complete_file(indexed: dict[str, dict[str, str]], label: str) -> bool:
        if set(indexed) != expected_ids:
            return False
        for record_id in expected_ids:
            if not row_text_matches(record_id, indexed):
                return False
            for field in LABEL_FIELDS:
                if indexed[record_id].get(field, "") not in ALLOWED[field]:
                    return False
        return not any(i["file"] == label and i["issue"] == "duplicate_record_id" for i in issues)

    a_complete = complete_file(a_index, "annotator_a")
    b_complete = complete_file(b_index, "annotator_b")
    status = "COMPLETE" if a_complete and b_complete else "INCOMPLETE"
    validation = {
        "status": status,
        "source_path": str(source_path),
        "annotator_a_path": str(annotator_a_path),
        "annotator_b_path": str(annotator_b_path),
        "source_row_count": len(source_rows),
        "source_unique_id_count": len(source_ids),
        "annotator_a_input_rows": len(a_rows),
        "annotator_b_input_rows": len(b_rows),
        "annotator_a_complete": a_complete,
        "annotator_b_complete": b_complete,
        "annotator_a_valid_label_counts": {field: len(valid_cells["annotator_a"][field]) for field in LABEL_FIELDS},
        "annotator_b_valid_label_counts": {field: len(valid_cells["annotator_b"][field]) for field in LABEL_FIELDS},
        "issues_count": len(issues),
        "issues": issues,
        "note": "A field metric uses only records with valid labels from both annotators and source-matching text. The report remains INCOMPLETE until both files contain one valid annotation for every source record.",
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "field_agreement.csv", ["field", "source_rows", "paired_valid_n", "matching_n", "disagreement_n", "percent_agreement", "cohens_kappa", "interpretation_note"], field_metrics)
    write_csv(output_dir / "disagreements.csv", ["record_id", "text", "field", "annotator_a_label", "annotator_b_label", "issue", "adjudication_status", "adjudicated_label", "adjudication_rationale"], disagreement_rows)
    write_csv(output_dir / "confusion_matrices.csv", ["field", "annotator_a_label", "annotator_b_label", "count"], confusion_rows)
    write_csv(output_dir / "validation_issues.csv", ["file", "record_id", "row", "issue", "detail"], issues)
    (output_dir / "validation_report.json").write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")

    report_lines = [
        "# LabelForge AI — Independent Annotation Agreement Report",
        "",
        f"**Status:** {status}",
        "",
        "## Method",
        "",
        f"- Source batch: `{source_path}` ({len(source_rows)} source rows; {len(source_ids)} unique record IDs).",
        f"- Annotator A: `{annotator_a_path}` — {'complete' if a_complete else 'incomplete or invalid'}.",
        f"- Annotator B: `{annotator_b_path}` — {'complete' if b_complete else 'incomplete or invalid'}.",
        "- Per-field exact agreement is the share of comparable records receiving the same label.",
        "- Cohen's kappa adjusts observed agreement for agreement expected from annotator label marginals.",
        "- Only labels that are allowed by the handbook and whose record text matches the source are included in a field's paired comparison.",
        "",
        "## Per-field results",
        "",
        "| Field | Paired valid n | Matches | Disagreements | Exact agreement | Cohen's kappa |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for metric in field_metrics:
        report_lines.append(
            f"| {metric['field']} | {metric['paired_valid_n']} | {metric['matching_n']} | {metric['disagreement_n']} | "
            f"{fmt_pct(metric['percent_agreement'])} | {fmt_kappa(metric['cohens_kappa'])} |"
        )
    report_lines += [
        "",
        "## Completion and disagreement summary",
        "",
        f"- Records with valid labels for all fields from both annotators: {len(complete_pair_ids)} of {len(source_ids)}.",
        f"- Records with complete labels and identical labels on all four fields: {overall_full_match} of {len(source_ids)}.",
        f"- Field-level disagreements ready for review: {len(disagreement_rows)}.",
        f"- Data validation issues recorded: {len(issues)}.",
        "",
        "## Interpretation and limitations",
        "",
        "- If status is INCOMPLETE, treat all metrics as interim. Complete both annotation files and rerun the script before publishing results.",
        "- Kappa can be undefined when expected chance agreement is 1.0 (for example, if both annotators use only one label for that field). The exact-agreement percentage is still reported when paired labels exist.",
        "- High agreement indicates consistency between these two annotation passes; it does not prove the labels are correct, clinically valid, or representative of real support data.",
        "- This workflow compares the independent annotations against each other. It does not compare them with `annotation_dataset.csv` and does not treat existing benchmark labels as independent human judgments.",
        "- Disagreements are not silently resolved. Use `disagreements.csv` to document adjudication, final decisions, and rationale.",
        "",
        "## Files generated",
        "",
        "- `field_agreement.csv` — exact agreement and Cohen's kappa by field.",
        "- `disagreements.csv` — each field-level disagreement, with adjudication columns.",
        "- `confusion_matrices.csv` — label-pair counts by field.",
        "- `validation_issues.csv` — missing/invalid labels, ID problems, and text mismatches.",
        "- `validation_report.json` — machine-readable completion and validation details.",
        "",
        "## Reproducibility",
        "",
        "Run the command recorded in the README using the saved source and independent annotation files. Preserve copies of the input CSVs and the handbook version used. Do not edit source text to make annotations align.",
        "",
    ]
    (output_dir / "agreement_report.md").write_text("\n".join(report_lines), encoding="utf-8")
    return validation


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=str(root / "data/unlabeled_batch.csv"), help="Unlabeled source CSV (default: project data/unlabeled_batch.csv)")
    parser.add_argument("--annotator-a", default=str(root / "data/annotator_a_template.csv"), help="Completed independent annotation CSV for annotator A")
    parser.add_argument("--annotator-b", default=str(root / "data/annotator_b_template.csv"), help="Completed independent annotation CSV for annotator B")
    parser.add_argument("--output-dir", default=str(root / "reports/independent_agreement"), help="Directory for report outputs")
    args = parser.parse_args()
    try:
        report = compare(Path(args.source), Path(args.annotator_a), Path(args.annotator_b), Path(args.output_dir))
    except (OSError, ValueError, csv.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({key: report[key] for key in ["status", "source_row_count", "annotator_a_complete", "annotator_b_complete", "issues_count"]}, indent=2))
    print(f"Report: {Path(args.output_dir) / 'agreement_report.md'}")
    return 0 if report["status"] == "COMPLETE" and report["issues_count"] == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
