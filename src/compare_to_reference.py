"""Compare one completed annotation pass with LabelForge AI's reference labels.

The reference dataset is a synthetic, authored portfolio benchmark. Metrics describe
agreement with that reference, not objective truth or inter-annotator reliability.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from compare_annotations import ALLOWED, LABEL_FIELDS, ANNOTATION_COLUMNS, SOURCE_COLUMNS, cohen_kappa, fmt_kappa, fmt_pct, read_csv, write_csv, blank, safe_pct


def compare_to_reference(annotations_path: Path, reference_path: Path, output_dir: Path) -> dict[str, Any]:
    for path in (annotations_path, reference_path):
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
    annotation_rows, annotation_headers = read_csv(annotations_path)
    reference_rows, reference_headers = read_csv(reference_path)
    issues: list[dict[str, Any]] = []
    required = ANNOTATION_COLUMNS
    for file_label, headers in [("annotations", annotation_headers), ("reference", reference_headers)]:
        missing = [column for column in required if column not in headers]
        if missing:
            issues.append({"file": file_label, "record_id": "", "issue": "missing_columns", "detail": f"Missing columns: {', '.join(missing)}"})
    if issues:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "validation_report.json").write_text(json.dumps({"status":"FAIL", "issues":issues}, indent=2), encoding="utf-8")
        raise ValueError("Input file is missing required columns. See validation_report.json.")

    def index(rows: list[dict[str, str]], label: str) -> tuple[dict[str, dict[str,str]], set[str]]:
        result: dict[str, dict[str,str]] = {}
        duplicates: set[str] = set()
        for row_number, row in enumerate(rows, start=2):
            record_id = row.get("record_id", "").strip()
            if not record_id:
                issues.append({"file": label, "record_id":"", "row":row_number, "issue":"missing_record_id", "detail":"Missing record_id."})
                continue
            if record_id in result:
                duplicates.add(record_id)
                issues.append({"file":label, "record_id":record_id, "row":row_number, "issue":"duplicate_record_id", "detail":"Duplicate ID; record excluded from comparisons."})
                continue
            result[record_id] = {k:(v or "").strip() for k,v in row.items()}
        for record_id in duplicates:
            result.pop(record_id, None)
        return result, duplicates

    annotation_map, annotation_duplicates = index(annotation_rows, "annotations")
    reference_map, reference_duplicates = index(reference_rows, "reference")
    annotation_ids, reference_ids = set(annotation_map), set(reference_map)
    for record_id in sorted(annotation_ids - reference_ids):
        issues.append({"file":"annotations", "record_id":record_id, "row":"", "issue":"unexpected_record_id", "detail":"ID not present in the reference dataset."})
    for record_id in sorted(reference_ids - annotation_ids):
        issues.append({"file":"annotations", "record_id":record_id, "row":"", "issue":"missing_record_id", "detail":"Reference record has no annotation row."})

    def labels_valid(row: dict[str, str], field: str) -> bool:
        value = row.get(field, "").strip()
        return not blank(value) and value in ALLOWED[field]

    field_rows = []
    disagreements = []
    confusion = []
    complete_valid = 0
    exact_all_fields = 0
    common_text_ids = sorted(annotation_ids & reference_ids)
    for record_id in common_text_ids:
        a, r = annotation_map[record_id], reference_map[record_id]
        if a.get("text", "").strip() != r.get("text", "").strip():
            issues.append({"file":"annotations", "record_id":record_id, "row":"", "issue":"text_mismatch", "detail":"Annotation text differs from reference text; record excluded from comparison."})
        for field in LABEL_FIELDS:
            val = a.get(field, "").strip()
            if blank(val):
                issues.append({"file":"annotations", "record_id":record_id, "row":"", "issue":"missing_label", "detail":f"Missing '{field}' label."})
            elif val not in ALLOWED[field]:
                issues.append({"file":"annotations", "record_id":record_id, "row":"", "issue":"invalid_label", "detail":f"'{val}' is not allowed for '{field}'."})
            ref_val = r.get(field, "").strip()
            if blank(ref_val) or ref_val not in ALLOWED[field]:
                issues.append({"file":"reference", "record_id":record_id, "row":"", "issue":"invalid_reference_label", "detail":f"Reference '{field}' label '{ref_val}' is missing or invalid."})

    usable_ids = [rid for rid in common_text_ids if annotation_map[rid].get("text", "").strip() == reference_map[rid].get("text", "").strip()]
    for record_id in usable_ids:
        a, r = annotation_map[record_id], reference_map[record_id]
        if all(labels_valid(a, field) and labels_valid(r, field) for field in LABEL_FIELDS):
            complete_valid += 1
            if all(a[field] == r[field] for field in LABEL_FIELDS):
                exact_all_fields += 1

    for field in LABEL_FIELDS:
        comparable = [rid for rid in usable_ids if labels_valid(annotation_map[rid], field) and labels_valid(reference_map[rid], field)]
        observed = [annotation_map[rid][field] for rid in comparable]
        expected = [reference_map[rid][field] for rid in comparable]
        matches = sum(x == y for x, y in zip(observed, expected))
        kappa = cohen_kappa(observed, expected, ALLOWED[field])
        field_rows.append({
            "field":field,
            "source_reference_rows":len(reference_rows),
            "paired_valid_n":len(comparable),
            "matches":matches,
            "disagreements":len(comparable)-matches,
            "exact_agreement_percent":round(safe_pct(matches,len(comparable)),3) if comparable else None,
            "cohens_kappa_vs_reference":round(kappa,6) if kappa is not None else None,
            "note":"Kappa is undefined when expected agreement is 1.0 or no comparable labels exist." if kappa is None else "Reference-agreement statistic; interpret in context of this synthetic benchmark.",
        })
        c = Counter(zip(observed, expected))
        for ann_label in sorted(ALLOWED[field]):
            for ref_label in sorted(ALLOWED[field]):
                if c[(ann_label,ref_label)]:
                    confusion.append({"field":field,"annotation_label":ann_label,"reference_label":ref_label,"count":c[(ann_label,ref_label)]})
        for rid in comparable:
            ann_label, ref_label = annotation_map[rid][field], reference_map[rid][field]
            if ann_label != ref_label:
                disagreements.append({
                    "record_id":rid, "text":reference_map[rid].get("text",""), "field":field,
                    "annotation_label":ann_label, "reference_label":ref_label,
                    "issue":"label_disagreement", "adjudication_status":"pending",
                    "final_label":"", "adjudication_rationale":""
                })

    is_complete = (
        annotation_ids == reference_ids
        and not annotation_duplicates and not reference_duplicates
        and len(annotation_rows) == len(reference_rows)
        and len(usable_ids) == len(reference_ids)
        and complete_valid == len(reference_ids)
    )
    status = "COMPLETE" if is_complete else "INCOMPLETE"
    validation = {
        "status":status,
        "annotations_path":str(annotations_path), "reference_path":str(reference_path),
        "annotation_row_count":len(annotation_rows), "reference_row_count":len(reference_rows),
        "annotation_complete_valid_rows":complete_valid,
        "exact_match_on_all_fields_rows":exact_all_fields,
        "issues_count":len(issues), "issues":issues,
        "note":"The reference labels are synthetic authored benchmark labels. Results measure agreement with this reference, not objective correctness or inter-annotator reliability. Complete status means the annotation file is structurally complete; it does not mean there are no label disagreements."
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir/"field_agreement.csv", ["field","source_reference_rows","paired_valid_n","matches","disagreements","exact_agreement_percent","cohens_kappa_vs_reference","note"], field_rows)
    write_csv(output_dir/"disagreements.csv", ["record_id","text","field","annotation_label","reference_label","issue","adjudication_status","final_label","adjudication_rationale"], disagreements)
    write_csv(output_dir/"confusion_matrices.csv", ["field","annotation_label","reference_label","count"], confusion)
    write_csv(output_dir/"validation_issues.csv", ["file","record_id","row","issue","detail"], issues)
    (output_dir/"validation_report.json").write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# LabelForge AI — Annotation Agreement with Reference Labels", "",
        f"**Status:** {status}", "",
        "## Scope and method", "",
        f"- Annotation file: `{annotations_path}` ({len(annotation_rows)} rows).",
        f"- Reference file: `{reference_path}` ({len(reference_rows)} rows).",
        "- Exact agreement is calculated separately for intent, sentiment, urgency, and review_required.",
        "- Cohen's kappa is also reported where mathematically defined.",
        "- Rows with text mismatch, missing labels, or invalid values are excluded from the affected field's comparison and recorded in validation output.",
        "", "## Per-field results", "",
        "| Field | Paired valid n | Matches | Disagreements | Exact agreement | Cohen's kappa vs reference |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for m in field_rows:
        lines.append(f"| {m['field']} | {m['paired_valid_n']} | {m['matches']} | {m['disagreements']} | {fmt_pct(m['exact_agreement_percent'])} | {fmt_kappa(m['cohens_kappa_vs_reference'])} |")
    lines += [
        "", "## Completion and disagreement summary", "",
        f"- Rows with valid annotation and reference labels for all four fields: {complete_valid} of {len(reference_ids)}.",
        f"- Rows matching the reference on all four fields: {exact_all_fields} of {len(reference_ids)}.",
        f"- Field-level label disagreements ready for review: {len(disagreements)}.",
        f"- Validation issues: {len(issues)}.",
        "", "## Interpretation and limitations", "",
        "- The existing reference labels are synthetic, authored portfolio labels, not an independently verified gold standard.",
        "- These results describe agreement with the reference dataset. They must not be described as inter-annotator agreement or proof of objective correctness.",
        "- Complete status means all expected rows and labels are present and valid. A complete file can still have disagreements.",
        "- Review disagreements manually against the handbook. Record adjudication and reasons rather than silently replacing labels.",
        "- Do not claim model improvement, production impact, or generalization based on this benchmark comparison.",
        "", "## Output files", "",
        "- `field_agreement.csv` — per-field exact agreement and kappa.",
        "- `disagreements.csv` — row-level mismatches, with adjudication columns.",
        "- `confusion_matrices.csv` — counts by annotator/reference label pair.",
        "- `validation_issues.csv` and `validation_report.json` — input quality and completeness details.",
        ""
    ]
    (output_dir/"agreement_report.md").write_text("\n".join(lines), encoding="utf-8")
    return validation


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", default=str(root/"data/unlabeled_batch.csv"), help="Completed annotation file (default: data/unlabeled_batch.csv)")
    parser.add_argument("--reference", default=str(root/"data/annotation_dataset.csv"), help="Reference-labeled dataset (default: data/annotation_dataset.csv)")
    parser.add_argument("--output-dir", default=str(root/"reports/reference_comparison"), help="Directory for output files")
    args = parser.parse_args()
    try:
        report = compare_to_reference(Path(args.annotations), Path(args.reference), Path(args.output_dir))
    except (OSError, ValueError, csv.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({key:report[key] for key in ["status","annotation_row_count","reference_row_count","annotation_complete_valid_rows","exact_match_on_all_fields_rows","issues_count"]}, indent=2))
    print(f"Report: {Path(args.output_dir)/'agreement_report.md'}")
    return 0 if report["status"] == "COMPLETE" else 1

if __name__ == "__main__":
    raise SystemExit(main())
