# LabelForge AI — Independent Annotation Agreement Report

**Status:** INCOMPLETE

## Method

- Source batch: `data/unlabeled_batch.csv` (60 source rows; 60 unique record IDs).
- Annotator A: `data/annotator_a_template.csv` — incomplete or invalid.
- Annotator B: `data/annotator_b_template.csv` — incomplete or invalid.
- Per-field exact agreement is the share of comparable records receiving the same label.
- Cohen's kappa adjusts observed agreement for agreement expected from annotator label marginals.
- Only labels that are allowed by the handbook and whose record text matches the source are included in a field's paired comparison.

## Per-field results

| Field | Paired valid n | Matches | Disagreements | Exact agreement | Cohen's kappa |
|---|---:|---:|---:|---:|---:|
| intent | 0 | 0 | 0 | N/A | undefined (insufficient variation or no paired labels) |
| sentiment | 0 | 0 | 0 | N/A | undefined (insufficient variation or no paired labels) |
| urgency | 0 | 0 | 0 | N/A | undefined (insufficient variation or no paired labels) |
| review_required | 0 | 0 | 0 | N/A | undefined (insufficient variation or no paired labels) |

## Completion and disagreement summary

- Records with valid labels for all fields from both annotators: 0 of 60.
- Records with complete labels and identical labels on all four fields: 0 of 60.
- Field-level disagreements ready for review: 0.
- Data validation issues recorded: 480.

## Interpretation and limitations

- If status is INCOMPLETE, treat all metrics as interim. Complete both annotation files and rerun the script before publishing results.
- Kappa can be undefined when expected chance agreement is 1.0 (for example, if both annotators use only one label for that field). The exact-agreement percentage is still reported when paired labels exist.
- High agreement indicates consistency between these two annotation passes; it does not prove the labels are correct, clinically valid, or representative of real support data.
- This workflow compares the independent annotations against each other. It does not compare them with `annotation_dataset.csv` and does not treat existing benchmark labels as independent human judgments.
- Disagreements are not silently resolved. Use `disagreements.csv` to document adjudication, final decisions, and rationale.

## Files generated

- `field_agreement.csv` — exact agreement and Cohen's kappa by field.
- `disagreements.csv` — each field-level disagreement, with adjudication columns.
- `confusion_matrices.csv` — label-pair counts by field.
- `validation_issues.csv` — missing/invalid labels, ID problems, and text mismatches.
- `validation_report.json` — machine-readable completion and validation details.

## Reproducibility

Run the command recorded in the README using the saved source and independent annotation files. Preserve copies of the input CSVs and the handbook version used. Do not edit source text to make annotations align.
