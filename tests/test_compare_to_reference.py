import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from compare_to_reference import compare_to_reference

FIELDS = ["record_id", "text", "intent", "sentiment", "urgency", "review_required"]


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


class ReferenceComparisonTests(unittest.TestCase):
    def test_reports_reference_agreement_and_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            ann = [
                {"record_id":"X1", "text":"Need receipt", "intent":"billing", "sentiment":"neutral", "urgency":"low", "review_required":"no_review"},
                {"record_id":"X2", "text":"Login fails", "intent":"account_access", "sentiment":"negative", "urgency":"medium", "review_required":"human_review"},
            ]
            ref = [dict(row) for row in ann]
            ref[1]["urgency"] = "high"
            a, r = folder/"annotations.csv", folder/"reference.csv"
            out = folder/"out"
            write_csv(a, ann)
            write_csv(r, ref)
            report = compare_to_reference(a, r, out)
            self.assertEqual(report["status"], "COMPLETE")
            with (out/"field_agreement.csv").open(newline="", encoding="utf-8") as f:
                metrics = {row["field"]:row for row in csv.DictReader(f)}
            self.assertEqual(metrics["urgency"]["paired_valid_n"], "2")
            self.assertEqual(metrics["urgency"]["disagreements"], "1")
            with (out/"disagreements.csv").open(newline="", encoding="utf-8") as f:
                mismatches = list(csv.DictReader(f))
            self.assertEqual(len(mismatches), 1)
            self.assertEqual(mismatches[0]["record_id"], "X2")
            self.assertEqual(mismatches[0]["field"], "urgency")

    def test_blank_annotations_are_not_reported_as_measured_agreement(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            blank_rows = [{"record_id":"X1", "text":"Need receipt", "intent":"", "sentiment":"", "urgency":"", "review_required":""}]
            ref_rows = [{"record_id":"X1", "text":"Need receipt", "intent":"billing", "sentiment":"neutral", "urgency":"low", "review_required":"no_review"}]
            a, r, out = folder/"annotations.csv", folder/"reference.csv", folder/"out"
            write_csv(a, blank_rows)
            write_csv(r, ref_rows)
            report = compare_to_reference(a, r, out)
            self.assertEqual(report["status"], "INCOMPLETE")
            with (out/"field_agreement.csv").open(newline="", encoding="utf-8") as f:
                metrics = list(csv.DictReader(f))
            self.assertEqual(metrics[0]["paired_valid_n"], "0")
            self.assertEqual(metrics[0]["exact_agreement_percent"], "")

if __name__ == "__main__":
    unittest.main()
