import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from compare_annotations import ALLOWED, cohen_kappa, compare


def save_csv(path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class AgreementComparisonTests(unittest.TestCase):
    def test_kappa_known_example(self):
        kappa = cohen_kappa(["x", "x", "y", "y"], ["x", "y", "y", "y"], {"x", "y"})
        self.assertAlmostEqual(kappa, 0.5)

    def test_kappa_undefined_when_expected_agreement_is_one(self):
        self.assertIsNone(cohen_kappa(["x", "x"], ["x", "x"], {"x", "y"}))

    def test_comparison_reports_agreement_and_disagreements(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "source.csv"
            a_path = folder / "a.csv"
            b_path = folder / "b.csv"
            out = folder / "out"
            source_rows = [
                {"record_id": "T1", "text": "Invoice missing"},
                {"record_id": "T2", "text": "Parcel late"},
                {"record_id": "T3", "text": "App crashes"},
            ]
            fields = ["record_id", "text", *ALLOWED.keys()]
            labels_a = [
                {"record_id":"T1", "text":"Invoice missing", "intent":"billing", "sentiment":"negative", "urgency":"medium", "review_required":"no_review"},
                {"record_id":"T2", "text":"Parcel late", "intent":"shipping", "sentiment":"negative", "urgency":"medium", "review_required":"no_review"},
                {"record_id":"T3", "text":"App crashes", "intent":"technical_support", "sentiment":"negative", "urgency":"high", "review_required":"human_review"},
            ]
            labels_b = [dict(row) for row in labels_a]
            labels_b[1]["sentiment"] = "mixed"
            save_csv(source, ["record_id", "text"], source_rows)
            save_csv(a_path, fields, labels_a)
            save_csv(b_path, fields, labels_b)
            report = compare(source, a_path, b_path, out)
            self.assertEqual(report["status"], "COMPLETE")
            self.assertEqual(report["issues_count"], 0)
            with (out / "field_agreement.csv").open(newline="", encoding="utf-8") as handle:
                metrics = {row["field"]: row for row in csv.DictReader(handle)}
            self.assertEqual(metrics["sentiment"]["paired_valid_n"], "3")
            self.assertEqual(metrics["sentiment"]["disagreement_n"], "1")
            with (out / "disagreements.csv").open(newline="", encoding="utf-8") as handle:
                disagreements = list(csv.DictReader(handle))
            self.assertEqual(len(disagreements), 1)
            self.assertEqual(disagreements[0]["record_id"], "T2")
            self.assertTrue((out / "agreement_report.md").exists())
            machine_report = json.loads((out / "validation_report.json").read_text(encoding="utf-8"))
            self.assertEqual(machine_report["status"], "COMPLETE")

    def test_incomplete_annotations_remain_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "source.csv"
            a_path = folder / "a.csv"
            b_path = folder / "b.csv"
            out = folder / "out"
            source_rows = [{"record_id":"T1", "text":"Invoice missing"}]
            template = [{"record_id":"T1", "text":"Invoice missing", "intent":"", "sentiment":"", "urgency":"", "review_required":""}]
            save_csv(source, ["record_id", "text"], source_rows)
            save_csv(a_path, ["record_id", "text", *ALLOWED.keys()], template)
            save_csv(b_path, ["record_id", "text", *ALLOWED.keys()], template)
            report = compare(source, a_path, b_path, out)
            self.assertEqual(report["status"], "INCOMPLETE")
            self.assertFalse(report["annotator_a_complete"])
            with (out / "field_agreement.csv").open(newline="", encoding="utf-8") as handle:
                metrics = list(csv.DictReader(handle))
            self.assertEqual(metrics[0]["paired_valid_n"], "0")
            self.assertEqual(metrics[0]["percent_agreement"], "")

if __name__ == "__main__":
    unittest.main()
