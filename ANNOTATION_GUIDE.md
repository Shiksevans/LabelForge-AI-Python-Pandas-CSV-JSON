# LabelForge AI Annotation Guide

## Purpose

This guide defines how customer support messages are labeled in the LabelForge AI demonstration dataset.

### 1. Intent

Choose the main reason for the customer's message.

account_access: Login, passwords, account details, or account access.

billing: Payments, invoices, charges, refunds, or receipts.

product_feedback: Opinions, suggestions, praise, or complaints about product features.

shipping: Delivery delays, tracking, packages, or transportation.

technical_support: Errors, crashes, malfunctions, or technical problems.

Choose the primary issue when a message mentions multiple topics.

### 2. Sentiment

Label the emotional tone expressed in the message.

positive: Clearly favorable, appreciative, or satisfied.

negative: Clearly dissatisfied, frustrated, or unhappy.

neutral: Mainly factual or a straightforward request without a clear emotional tone.

mixed: Contains meaningful positive and negative sentiment.

### 3. Urgency

Judge how quickly the issue appears to require attention.

low: Routine questions or requests without an apparent immediate impact.

medium: An issue needs attention but does not appear immediately critical.

high: A significant problem, blocked account access, serious payment issue, or major malfunction requiring prompt attention.

Determine urgency from the message context, not sentiment alone.

##### 4. Review Required

human_review: The issue appears to require human investigation, judgment, or intervention.

no_review: The message appears suitable for routine handling without additional human investigation.

Consider complexity, impact, ambiguity, and potential consequences.

Annotation Principles

Read the entire message before assigning labels.

Use only the permitted label values defined in this guide.

Preserve the original record_id and message text.

For independent annotation, do not consult another annotator's labels or the reference labels while labeling.

If a message is ambiguous, choose the best-supported interpretation and document the uncertainty separately.

Never change labels merely to increase agreement scores.

Record any revisions to this guide so the workflow remains reproducible.