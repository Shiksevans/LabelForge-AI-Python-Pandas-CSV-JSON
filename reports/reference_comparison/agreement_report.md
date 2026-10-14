# LabelForge AI — Annotation Agreement with Reference Labels

**Status:** COMPLETE

## Scope and method

- Annotation file: `C:\Users\BEST\OneDrive\Desktop\labelforge_ai\data\unlabeled_batch.csv` (60 rows).
- Reference file: `C:\Users\BEST\OneDrive\Desktop\labelforge_ai\data\annotation_dataset.csv` (60 rows).
- Exact agreement is calculated separately for intent, sentiment, urgency, and review_required.
- Cohen's kappa is also reported where mathematically defined.
- Rows with text mismatch, missing labels, or invalid values are excluded from the affected field's comparison and recorded in validation output.

## Per-field results

| Field | Paired valid n | Matches | Disagreements | Exact agreement | Cohen's kappa vs reference |
|---|---:|---:|---:|---:|---:|
| intent | 60 | 60 | 0 | 100.0% | 1.000 |
| sentiment | 60 | 60 | 0 | 100.0% | 1.000 |
| urgency | 60 | 60 | 0 | 100.0% | 1.000 |
| review_required | 60 | 60 | 0 | 100.0% | 1.000 |

## Completion and disagreement summary

- Rows with valid annotation and reference labels for all four fields: 60 of 60.
- Rows matching the reference on all four fields: 60 of 60.
- Field-level label disagreements ready for review: 0.
- Validation issues: 0.

## Interpretation and limitations

- The existing reference labels are synthetic, authored portfolio labels, not an independently verified gold standard.
- These results describe agreement with the reference dataset. They must not be described as inter-annotator agreement or proof of objective correctness.
- Complete status means all expected rows and labels are present and valid. A complete file can still have disagreements.
- Review disagreements manually against the handbook. Record adjudication and reasons rather than silently replacing labels.
- Do not claim model improvement, production impact, or generalization based on this benchmark comparison.

## Output files

- `field_agreement.csv` — per-field exact agreement and kappa.
- `disagreements.csv` — row-level mismatches, with adjudication columns.
- `confusion_matrices.csv` — counts by annotator/reference label pair.
- `validation_issues.csv` and `validation_report.json` — input quality and completeness details.
