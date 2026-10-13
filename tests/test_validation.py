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

if __name__ == "__main__":
    unittest.main()
