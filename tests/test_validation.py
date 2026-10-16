import unittest
import pandas as pd
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from validate_dataset import validate_dataframe

class ValidationTests(unittest.TestCase):
    def test_valid_minimal_row_passes(self):
        df = pd.DataFrame([{
            "record_id": "T001", "text": "Where is my invoice?",
            "intent": "billing", "sentiment": "neutral",
            "urgency": "low", "review_required": "no_review"
        }])
        self.assertEqual(validate_dataframe(df)["status"], "PASS")

    def test_custom_schema_rejects_invalid_label(self):
        df = pd.DataFrame([{
            "record_id": "T002",
            "text": "I need customer support",
            "category": "billing",
        }])

        report = validate_dataframe(
            df,
            allowed={"category": {"support", "sales"}},
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("category", report["invalid_label_details"])

    def test_invalid_label_fails(self):
        df = pd.DataFrame([{
            "record_id": "T001", "text": "Where is my invoice?",
            "intent": "money", "sentiment": "neutral",
            "urgency": "low", "review_required": "no_review"
        }])
        report = validate_dataframe(df)
        self.assertEqual(report["status"], "FAIL")
        self.assertGreater(report["error_count"], 0)

    def test_duplicate_ids_fail(self):
        row = {
            "record_id": "T001", "text": "Where is my invoice?",
            "intent": "billing", "sentiment": "neutral",
            "urgency": "low", "review_required": "no_review"
        }
        report = validate_dataframe(pd.DataFrame([row, row]))
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["duplicate_id_rows"], 2)

    def test_empty_text_fails(self):
        df = pd.DataFrame([{
            "record_id": "T001", "text": "  ",
            "intent": "billing", "sentiment": "neutral",
            "urgency": "low", "review_required": "no_review"
        }])
        self.assertEqual(validate_dataframe(df)["status"], "FAIL")

    def test_missing_record_id_fails(self):
        row = {
            "record_id": None, "text": "Where is my invoice?",
            "intent": "billing", "sentiment": "neutral",
            "urgency": "low", "review_required": "no_review"
        }
        report = validate_dataframe(pd.DataFrame([row]))
        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            "missing_record_ids",
            [error["type"] for error in report["errors"]]
        )

    def test_blank_record_id_fails(self):
        row = {
            "record_id": "   ", "text": "Where is my invoice?",
            "intent": "billing", "sentiment": "neutral",
            "urgency": "low", "review_required": "no_review"
        }
        report = validate_dataframe(pd.DataFrame([row]))
        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            "missing_record_ids",
            [error["type"] for error in report["errors"]]
        )

    def test_whitespace_only_label_is_reported_as_missing(self):
        row = {
            "record_id": "T001", "text": "Where is my invoice?",
            "intent": "   ", "sentiment": "neutral",
            "urgency": "low", "review_required": "no_review"
        }
        report = validate_dataframe(pd.DataFrame([row]))
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(
            report["invalid_label_details"]["intent"]["null_count"], 1
        )
        self.assertEqual(
            report["invalid_label_details"]["intent"]["invalid_values"], []
        )

    def test_whitespace_padded_valid_label_fails(self):
        row = {
            "record_id": "T001", "text": "Where is my invoice?",
            "intent": " billing ", "sentiment": "neutral",
            "urgency": "low", "review_required": "no_review"
        }
        report = validate_dataframe(pd.DataFrame([row]))
        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            " billing ",
            report["invalid_label_details"]["intent"]["invalid_values"]
        )

    def test_custom_schema_passes(self):
        df = pd.DataFrame([{
            "record_id": "T001",
            "text": "I need customer support",
            "category": "support",
        }])

        report = validate_dataframe(
            df,
            allowed={"category": {"support", "sales"}},
        )

        self.assertEqual(report["status"], "PASS")
        self.assertIn("category", report["label_distributions"])
        self.assertNotIn("intent", report["label_distributions"])



if __name__ == "__main__":
    unittest.main()
