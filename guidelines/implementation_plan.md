# Implementation Plan

## Phase 1 — Define
- Read the annotation handbook.
- Confirm label values and decision rules.
- Freeze dataset version 1.0 before evaluating quality.

## Phase 2 — Annotate
- Review the 60 synthetic records.
- For a stronger portfolio demonstration, hide the labels in `unlabeled_batch.csv` and independently annotate a subset.
- Record difficult cases and reasons for uncertainty.

## Phase 3 — Validate
- Run the structural validator.
- Review errors rather than changing data blindly.
- Save the JSON report and record the code/data version.

## Phase 4 — Measure semantic quality
- Select 15–20 rows randomly.
- Have a second annotator label them without seeing the first labels, or wait a reasonable interval and conduct a documented blind second pass.
- Calculate exact agreement for each field.
- If there are two independent annotators and enough category variation, calculate Cohen's kappa with an appropriate library or spreadsheet.
- Adjudicate disagreements and update the guideline version.

## Phase 5 — Publish
- Add a screenshot of the report or a small chart of label distributions.
- Include three worked examples and one anonymized disagreement case.
- Publish CSVs, code, handbook, report, and limitations.
- Keep the repository transparent about synthetic data and independent status.

## Acceptance criteria (targets, not results)
- 100% required columns present.
- 0 missing labels.
- 0 duplicate record IDs.
- 0 invalid category values.
- Every row has non-empty text.
- All disagreements in the second-pass sample are logged and resolved or explicitly left unresolved.
- README states that structural validation does not prove semantic correctness.
