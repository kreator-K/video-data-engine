# Frontend copy rule

Hard rule: never display em dashes (Unicode U+2014) anywhere in the frontend.
This includes insights, charts, labels, headings, source titles, evidence,
status messages, imported reports, generated content, and the browser title.
Use a comma, colon, parentheses, or a standard hyphen instead.
Normalize dynamic display text at the rendering boundary without altering raw
evidence, identifiers, URLs, or backend analysis. Keep this rule enforced by the
frontend build checks. Do not introduce em dashes in new frontend copy.
