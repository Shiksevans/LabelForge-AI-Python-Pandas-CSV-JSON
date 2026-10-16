import json
import unittest
import tempfile
from pathlib import Path

from src.schema_config import (
    DEFAULT_ALLOWED,
    load_schema,
    validate_schema,
)


class SchemaConfigTests(unittest.TestCase):
    def test_default_schema_contains_expected_fields(self):
        self.assertEqual(
            set(DEFAULT_ALLOWED),
            {"intent", "sentiment", "urgency", "review_required"},
        )

    def test_valid_custom_schema_is_accepted(self):
        result = validate_schema({
            "category": ["support", "sales"],
        })
        self.assertEqual(result, {
            "category": {"support", "sales"},
        })

    def test_empty_schema_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_schema({})

    def test_empty_label_list_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_schema({"category": []})

    def test_blank_label_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_schema({"category": ["support", " "]})

    def test_duplicate_labels_are_rejected(self):
        with self.assertRaises(ValueError):
            validate_schema({"category": ["support", "support"]})

    def test_reserved_field_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_schema({"record_id": ["A", "B"]})

    def test_json_schema_can_be_loaded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_path = Path(temp_dir) / "schema.json"
            schema_path.write_text(
                json.dumps({"category": ["support", "sales"]}),
                encoding="utf-8",
            )

            result = load_schema(schema_path)

            self.assertEqual(
                result,
                {"category": {"support", "sales"}},
            )

    def test_invalid_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_path = Path(temp_dir) / "schema.json"
            schema_path.write_text("{invalid", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_schema(schema_path)


if __name__ == "__main__":
    unittest.main()
