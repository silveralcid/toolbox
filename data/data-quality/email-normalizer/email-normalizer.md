# Email Normalizer

## Problem It Solves

Converts raw email inputs into a consistent, matchable key for dedupe, routing, and record lookup. Flags invalid or suspicious email inputs so workflows can branch cleanly.

## Best Use Cases

### Use Case #1

Pre-dedupe key normalization before searching CRM for existing contacts/leads.

### Use Case #2

Inbound routing and ownership assignment using a consistent email key.

### Use Case #3

Outbound readiness validation to block sequences when email is invalid.

## Inputs

### Schema

This script reads a source object (Zapier `inputData` or n8n `item.json`) and extracts only the email fields you configure. Whitespace Cleaner is assumed to run before this, so values should already be trimmed and de-junked.

| Config item | Type   | Meaning                                          |
| ----------- | ------ | ------------------------------------------------ |
| FIELD_MAP   | object | Output key → input path (dot paths supported)    |
| DEFAULTS    | object | Behavior controls (lowercase, extract, validate) |

## Outputs

### Schema

Returns the original record merged with normalized email fields by default.

| Field                | Type          | Notes                                                         |
| -------------------- | ------------- | ------------------------------------------------------------- |
| (mapped output keys) | string | null | Normalized email value                                        |
| email_warnings       | string[]      | Optional flags (only when enabled)                            |
| email_changed_fields | string[]      | Optional list of output keys that changed (only when enabled) |

## Operator Guide

### Config you edit at the top

| Setting             | Recommended default | Purpose                                                                              |
| ------------------- | ------------------- | ------------------------------------------------------------------------------------ |
| OUTPUT_MODE         | `merge`             | `merge` adds normalized fields onto the original object, `only` returns only outputs |
| EMPTY_TO_NULL       | `true`              | Converts empty strings after normalization to null                                   |
| LOWERCASE           | `true`              | Lowercases the email                                                                 |
| EXTRACT_EMAIL       | `false`             | Attempts to pull an email out of strings like `Bob <bob@x.com>`                      |
| VALIDATE_FORMAT     | `true`              | Applies conservative format validation                                               |
| EMIT_CHANGED_FIELDS | `true`              | Returns `email_changed_fields`                                                       |
| EMIT_WARNINGS       | `true`              | Returns `email_warnings`                                                             |
| COERCE_NON_STRING   | `false`             | If true, converts non-string values to strings before processing                     |

### FIELD_MAP patterns

| Pattern            | Example                                                        | Result                                 |
| ------------------ | -------------------------------------------------------------- | -------------------------------------- |
| Simple top-level   | `{ email_norm: "email" }`                                      | Writes `email_norm`                    |
| Nested input path  | `{ email_norm: "contact.email" }`                              | Reads nested value safely              |
| Overwrite existing | `{ email: "email" }`                                           | Replaces `email` with normalized value |
| Multiple emails    | `{ email_norm: "email", billing_email_norm: "billing.email" }` | Normalizes multiple fields             |

### Minimal steps (Zapier and n8n)

| Step | Action                                                   | Outcome                                     |
| ---- | -------------------------------------------------------- | ------------------------------------------- |
| 1    | Run Whitespace Cleaner first on your email fields        | Removes trailing spaces and invisible chars |
| 2    | Place this Email Normalizer immediately after            | Produces a consistent match key             |
| 3    | Write back normalized outputs to CRM or use for searches | Reliable dedupe and lookups                 |
| 4    | Branch on warnings and null outputs                      | Review or block outbound when invalid       |

## Logic Reference

### Normalization rules applied per field

| Rule                     | What it does                                        | Example                                 |
| ------------------------ | --------------------------------------------------- | --------------------------------------- |
| Lowercase                | Converts email to lowercase                         | `TEST@EXAMPLE.COM` → `test@example.com` |
| Extract email (optional) | Finds first email-like substring inside larger text | `Bob <bob@x.com>` → `bob@x.com`         |
| Validate format          | Conservative format check (not deliverability)      | `bob@x` → invalid                       |
| Empty to null            | Converts `""` to null                               | `""` → null                             |

### Warnings (optional)

| Warning          | When it happens                                                  |
| ---------------- | ---------------------------------------------------------------- |
| FIELD_MISSING    | Mapped input path not found                                      |
| VALUE_NOT_STRING | Field exists but is not a string and coercion is off             |
| EMAIL_EXTRACTED  | EXTRACT_EMAIL is on and an email was pulled from a larger string |
| INVALID_EMAIL    | Email fails format validation                                    |
| CLEANED_TO_EMPTY | Normalization produced empty/null output                         |

## Edge Cases

| Scenario                            | Expected behavior                                                |
| ----------------------------------- | ---------------------------------------------------------------- |
| Email contains display-name wrapper | Valid only if EXTRACT_EMAIL is enabled and extraction succeeds   |
| Multiple emails in one field        | Extraction will take the first email-like match when enabled     |
| Internationalized emails            | Conservative validation may flag some valid-but-uncommon formats |
| Missing field                       | Output key is set to null and FIELD_MISSING may be emitted       |

## Testing

### Test Cases

| Input              | Config               | Expected output               |
| ------------------ | -------------------- | ----------------------------- |
| `TEST@Example.com` | lowercase + validate | `test@example.com`            |
| `Bob <bob@x.com>`  | extract + validate   | `bob@x.com` + EMAIL_EXTRACTED |
| `bob@x`            | validate             | null + INVALID_EMAIL          |
| `""`               | empty_to_null        | null + CLEANED_TO_EMPTY       |
| field missing      | warnings on          | null + FIELD_MISSING          |

### Optional Automation

| Automation              | Outcome                                       |
| ----------------------- | --------------------------------------------- |
| Pre-write normalization | Prevents inconsistent emails in CRM           |
| Review on invalid       | Creates task/ticket when INVALID_EMAIL        |
| Outbound block          | Stops sequences when normalized email is null |