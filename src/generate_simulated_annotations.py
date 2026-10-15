"""Generate simulated annotations for LabelForge AI workflow testing.

These are synthetic demonstration labels, not real human annotations.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "unlabeled_source.csv"
OUTPUT_A = ROOT / "data" / "simulated_annotator_a.csv"
OUTPUT_B = ROOT / "data" / "simulated_annotator_b.csv"

FIELDS = [
    "record_id",
    "text",
    "intent",
    "sentiment",
    "urgency",
    "review_required",
]


def classify(text):
    """Apply simple rules to generate demonstration labels."""
    t = text.lower()

    # Intent
    if any(w in t for w in [
        "charge", "payment", "invoice", "receipt", "refund",
        "billing", "subscription", "monthly plan", "price"
    ]):
        intent = "billing"
    elif any(w in t for w in [
        "package", "delivery", "delivered", "shipping",
        "tracking", "shipment", "arrived", "order"
    ]):
        intent = "shipping"
    elif any(w in t for w in [
        "login", "log in", "password", "account",
        "sign in", "email address", "username"
    ]):
        intent = "account_access"
    elif any(w in t for w in [
        "crash", "error", "bug", "not working",
        "doesn't work", "does not work", "failed",
        "technical", "settings page"
    ]):
        intent = "technical_support"
    else:
        intent = "product_feedback"

    # Sentiment
    positive_words = [
        "love", "thank", "thanks", "great", "excellent",
        "perfectly", "easier", "happy", "pleased"
    ]
    negative_words = [
        "angry", "frustrated", "broken", "crash", "error",
        "failed", "late", "wrong", "charged twice", "cannot",
        "can't", "unable", "disappointed", "terrible"
    ]

    positive = any(w in t for w in positive_words)
    negative = any(w in t for w in negative_words)

    if positive and negative:
        sentiment = "mixed"
    elif negative:
        sentiment = "negative"
    elif positive:
        sentiment = "positive"
    else:
        sentiment = "neutral"

    # Urgency
    high_words = [
        "charged twice", "cannot log in", "can't log in",
        "crashes every time", "completely blocked",
        "urgent", "immediately", "security breach"
    ]
    medium_words = [
        "late", "problem", "issue", "failed", "error",
        "not working", "doesn't work", "does not work"
    ]

    if any(w in t for w in high_words):
        urgency = "high"
    elif any(w in t for w in medium_words):
        urgency = "medium"
    else:
        urgency = "low"

    review_required = (
        "human_review" if urgency == "high" else "no_review"
    )

    return {
        "intent": intent,
        "sentiment": sentiment,
        "urgency": urgency,
        "review_required": review_required,
    }


def main():
    with SOURCE.open(
        "r", newline="", encoding="utf-8-sig"
    ) as f:
        source_rows = list(csv.DictReader(f))

    if not source_rows:
        raise ValueError("The source file contains no records.")

    if any(
        not row.get("record_id") or not row.get("text")
        for row in source_rows
    ):
        raise ValueError("A source record is missing its ID or text.")

    ids = [row["record_id"] for row in source_rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate record IDs found in the source.")

    annotator_a = []
    annotator_b = []

    # Deliberate simulated differences to test disagreement reporting.
    variations = {
        "LF003": {"urgency": "low"},
        "LF004": {"review_required": "no_review"},
        "LF008": {"sentiment": "positive"},
        "LF012": {"intent": "technical_support"},
        "LF018": {"urgency": "medium"},
        "LF025": {"review_required": "human_review"},
    }

    for row in source_rows:
        labels_a = classify(row["text"])
        labels_b = labels_a.copy()
        labels_b.update(variations.get(row["record_id"], {}))

        annotator_a.append({
            "record_id": row["record_id"],
            "text": row["text"],
            **labels_a,
        })
        annotator_b.append({
            "record_id": row["record_id"],
            "text": row["text"],
            **labels_b,
        })

    for path, rows in [
        (OUTPUT_A, annotator_a),
        (OUTPUT_B, annotator_b),
    ]:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    print("Simulated annotation files created successfully.")
    print(f"Source records: {len(source_rows)}")
    print(f"Annotator A: {OUTPUT_A.relative_to(ROOT)}")
    print(f"Annotator B: {OUTPUT_B.relative_to(ROOT)}")
    print("Note: These labels are synthetic, not real human annotations.")


if __name__ == "__main__":
    main()
