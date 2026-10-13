# LabelForge AI — Annotation Handbook
Version: 1.0
Dataset: Synthetic customer-support messages
Status: Portfolio demonstration; no real customer data

## 1. Purpose
Assign each message one intent, one sentiment, one urgency level, and a review-routing label. Labels describe the message as written, not assumptions about the customer.

## 2. Label schema

### intent (exactly one)
- `billing`: invoices, charges, payments, refunds, subscriptions, fees.
- `shipping`: orders, parcels, delivery, tracking, couriers, replacements in transit.
- `technical_support`: app/site errors, bugs, performance, setup failures, product operation.
- `account_access`: login, passwords, identity verification, profile details, account security, privacy requests.
- `product_feedback`: opinions, feature requests, usability, product satisfaction or dissatisfaction not primarily an account/technical incident.

Decision rule: choose the primary action/problem the message asks about. If an issue spans categories, choose the most direct operational issue (e.g. app crashes -> technical_support, even if it blocks checkout).

### sentiment (exactly one)
- `positive`: praise or satisfaction without a meaningful negative concern.
- `negative`: dissatisfaction, complaint, frustration, or concern without meaningful positive balance.
- `neutral`: information request or factual statement without clear positive/negative evaluation.
- `mixed`: both meaningful positive and negative evaluation, or a clearly stated benefit and drawback.

Decision rule: don't infer sentiment from punctuation alone. A request can be neutral even if it concerns a problem.

### urgency (exactly one)
- `high`: account compromise/security concern; potentially consequential payment problem; blocked access with repeated failure; missing parcel marked delivered; or a major service failure likely to need prompt triage.
- `medium`: service problem or customer impact needing attention, but no defined high-urgency trigger.
- `low`: routine question, praise, suggestion, or request without signs of immediate impact.

This is a routing label for this fictional support dataset, not a real-world SLA or safety assessment.

### review_required (exactly one)
- `human_review`: ambiguous/multi-issue messages, high-urgency triggers, material financial/account security concerns, or a case where automated routing could materially misdirect support.
- `no_review`: clear, routine message that fits the labels without an obvious escalation trigger.

Use `human_review` when uncertainty could affect routing. Do not use it simply because a message is negative.

## 3. Annotation workflow
1. Read the full message.
2. Identify the primary issue/action requested.
3. Assign intent.
4. Assign sentiment based on the whole message.
5. Assign urgency using the explicit triggers above.
6. Assign review_required using the review rules.
7. Re-read the message and check all labels against the schema.
8. If genuinely unresolved, record the case in an adjudication log instead of inventing certainty.

## 4. Edge cases
- “The delivery was late, but the product is excellent” -> shipping, mixed.
- “I cannot tell whether the payment went through; the page froze” -> billing if payment uncertainty is the main issue; high urgency; human review.
- “The app is slow on my phone, but fine on my laptop” -> technical_support, mixed, medium.
- “Please stop promotional emails” -> account_access, negative (explicit opt-out request signals dissatisfaction in this schema), medium, no_review if otherwise clear.
- “My account may have been accessed without permission” -> account_access, negative, high, human_review.
- Sarcasm, multiple unrelated requests, or unclear primary intent -> document ambiguity and request adjudication.

## 5. Quality rules
- Only use allowed label values.
- Every record must have a unique `record_id`.
- Never add personal data or infer protected traits.
- Do not silently modify source text.
- Keep an adjudication log with original label, proposed change, reason, and reviewer/date.
- For agreement measurement, use two independent passes or a second reviewer; do not copy the first pass and call it independent.

## 6. Limitations
The dataset is synthetic and small. Labels encode this handbook's conventions and should not be treated as universal truths. Urgency and review labels are simulated routing decisions. Before real deployment, a domain owner must validate the taxonomy and thresholds.
