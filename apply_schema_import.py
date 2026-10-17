from pathlib import Path

path = Path("src/compare_annotations.py")
text = path.read_text(encoding="utf-8")

start_marker = "from typing import Any"
end_marker = "LABEL_FIELDS = list(ALLOWED)"

if text.count(start_marker) != 1 or text.count(end_marker) != 1:
    raise SystemExit("STOP: Unexpected file structure. No changes made.")

start = text.index(start_marker)
end = text.index(end_marker)

if start >= end:
    raise SystemExit("STOP: Unexpected code order. No changes made.")

replacement = (
    "from typing import Any\n\n"
    "from schema_config import DEFAULT_ALLOWED, load_schema\n\n"
    "ALLOWED = DEFAULT_ALLOWED\n"
)

path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")
print("Shared schema import updated successfully.")
