# Worked Examples

These are examples of how the handbook is applied. The dataset itself is synthetic.

## Example A — Mixed sentiment
**Text:** “The delivery was late, but the product works perfectly.”
- Intent: `shipping`
- Sentiment: `mixed`
- Urgency: `medium`
- Review required: `no_review`
- Rationale: The delivery is the primary issue; the message contains a clear drawback and a positive product statement. No high-urgency trigger is present.

## Example B — Payment uncertainty
**Text:** “I cannot tell whether my payment went through; the page froze.”
- Intent: `billing`
- Sentiment: `neutral`
- Urgency: `high`
- Review required: `human_review`
- Rationale: Payment uncertainty is the main concern, and the frozen page may cause a consequential duplicate or incomplete transaction. This is a simulated routing rule.

## Example C — Account security
**Text:** “I think someone else has accessed my account without permission.”
- Intent: `account_access`
- Sentiment: `negative`
- Urgency: `high`
- Review required: `human_review`
- Rationale: The message expresses concern about unauthorized access. It meets the handbook's high-urgency and human-review triggers.

## Example D — Positive and negative product feedback
**Text:** “I love the service, but the latest update removed my favorite feature.”
- Intent: `product_feedback`
- Sentiment: `mixed`
- Urgency: `medium`
- Review required: `human_review`
- Rationale: A positive statement and a meaningful complaint coexist. Review is requested because the issue may require a product-feedback or feature-restoration decision.

## Example E — Routine information request
**Text:** “How can I download the receipt for last month's invoice?”
- Intent: `billing`
- Sentiment: `neutral`
- Urgency: `low`
- Review required: `no_review`
- Rationale: A clear, routine invoice-related request without a stated complaint or escalation trigger.

## Adjudication log template
| record_id | field | original label | proposed label | rationale | reviewer | date |
|---|---|---|---|---|---|---|
| LF___ | sentiment |  |  |  |  | YYYY-MM-DD |

Only fill this log when a real review or adjudication has occurred.
