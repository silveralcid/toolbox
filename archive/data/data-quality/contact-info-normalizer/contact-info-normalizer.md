# Contact Info Normalizer

## Problem It Solves

Standardizes identity fields (email, phone, name) so matching, dedupe, routing, and personalization are consistent across tools like CRMs, forms, and inbound lead sources. Flags invalid or incomplete inputs so workflows can branch instead of silently writing bad data.

## Best Use Cases

### Use Case #1

Normalize identity fields before searching the CRM for an existing record.

### Use Case #2

Normalize inbound leads before routing or assigning ownership.

### Use Case #3

Validate outbound readiness before sending email/SMS sequences.

## Inputs

### Schema

`{ email, phone, first, last, full_name, default_country }`

| Field           | Type   | Required | Notes                                                                        |
| --------------- | ------ | -------: | ---------------------------------------------------------------------------- |
| email           | string |       No | Raw email value from form/CRM/webhook                                        |
| phone           | string |       No | Raw phone value from form/CRM/webhook                                        |
| first           | string |       No | Raw first name                                                               |
| last            | string |       No | Raw last name                                                                |
| full_name       | string |       No | Raw full name when first/last not available                                  |
| default_country | string |       No | Used only when phone has no country code; recommended `"US"` for US-only ops |

## Outputs

### Schema

`{ email_norm, phone_norm, first, last, full_name, warnings[] }`

| Field      | Type          | Notes                                                                   |
| ---------- | ------------- | ----------------------------------------------------------------------- |
| email_norm | string | null | Lowercased + format-validated email, or null if invalid/missing         |
| phone_norm | string | null | Best-effort normalized phone (E.164-like), or null if invalid/ambiguous |
| first      | string | null | Cleaned first name or derived from full_name                            |
| last       | string | null | Cleaned last name or derived from full_name                             |
| full_name  | string | null | Cleaned full name or derived from first/last                            |
| warnings   | string[]      | Machine-actionable flags for workflow branching                         |

## Operator Guide

Instructions for BizOps users implementing this as a Zapier “Code” step or n8n “Code” node.

| Step | Action                                                                                            | Outcome                                                  |
| ---- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| 1    | Place the Code step/node immediately after your trigger (form submit, webhook, CRM create/update) | Normalization happens before CRM writeback and routing   |
| 2    | Map your source fields into the input schema keys                                                 | Predictable behavior across sources                      |
| 3    | Return the output schema keys as top-level fields                                                 | Downstream steps can reference normalized values cleanly |
| 4    | Write back only normalized fields you trust                                                       | Prevents overwriting good data with blanks               |
| 5    | Add branching using `warnings[]` and null checks                                                  | Automated QA, review queues, or enrichment               |

### Mapping Guidance

| Source situation               | What to map                                 | Notes                                     |
| ------------------------------ | ------------------------------------------- | ----------------------------------------- |
| You have separate name fields  | `first`, `last`, optionally `full_name`     | Prefer `first`/`last` as authoritative    |
| You only have full name        | `full_name`                                 | Script will attempt best-effort split     |
| You have multiple phone fields | `phone`                                     | Choose primary mobile if available        |
| You operate US-only            | `default_country = "US"`                    | Enables normalization of 10-digit numbers |
| You operate internationally    | Require `phone` to include `+` country code | Otherwise route to enrichment/review      |

### Writeback Strategy

| Field                | Recommended writeback behavior                                                                |
| -------------------- | --------------------------------------------------------------------------------------------- |
| email_norm           | Write to Email or a dedicated “Normalized Email” field                                        |
| phone_norm           | Write to Phone or a dedicated “Normalized Phone” field                                        |
| first/last/full_name | Write cleaned values if present; do not overwrite existing with null                          |
| warnings[]           | Write to a “Data Quality Warnings” field (text or multi-select) for visibility and automation |

### Branching Recipes

| Condition                                                     | Recommended action                         |
| ------------------------------------------------------------- | ------------------------------------------ |
| `email_norm` is null and email was provided                   | Create a review task, stop outbound email  |
| `phone_norm` is null and phone was provided                   | Create a review task, stop outbound SMS    |
| warnings contains `PHONE_NEEDS_COUNTRY`                       | Send to enrichment or request country code |
| warnings contains `MISSING_NAME`                              | Enrich name or route to manual cleanup     |
| no warnings and at least one of email_norm/phone_norm present | Continue to dedupe search and routing      |

## Logic Reference

Explains how the script behaves so operators can predict outcomes and set expectations.

### Normalization Rules

| Area            | Rule                                                                           | Result                                        |
| --------------- | ------------------------------------------------------------------------------ | --------------------------------------------- |
| General         | Trim all strings; convert empty strings to null                                | Avoids blank overwrites                       |
| Email           | Lowercase and apply conservative format validation                             | Invalid formats become null + `INVALID_EMAIL` |
| Phone           | Strip non-digits; allow leading `+`; optionally convert `00` prefix to `+`     | Produces an E.164-like output when possible   |
| Phone inference | Only infer country for domestic-only ops using `default_country`               | Otherwise null + `PHONE_NEEDS_COUNTRY`        |
| Names           | Collapse spaces; strip edge punctuation; preserve internal hyphens/apostrophes | Cleaner, stable display names                 |
| Derivation      | Build full_name from first/last if missing                                     | full_name becomes “first last” when available |
| Splitting       | If first/last missing and full_name exists, split best-effort                  | Single token becomes first + `MISSING_LAST`   |

### Warning Codes

| Warning               | Meaning                                                | Typical workflow action                 |
| --------------------- | ------------------------------------------------------ | --------------------------------------- |
| INVALID_EMAIL         | Email fails format validation                          | Block outbound email; review/enrich     |
| INVALID_PHONE         | Phone fails basic validity rules                       | Block SMS; review/enrich                |
| PHONE_NEEDS_COUNTRY   | Phone has no `+` and country cannot be inferred safely | Enrich country or request proper format |
| MISSING_NAME          | No usable first/last/full_name                         | Enrich name or route to cleanup         |
| MISSING_LAST          | Only one name token was provided                       | Optional cleanup depending on use case  |
| MULTIPLE_PHONES_FOUND | Phone field appears to contain multiple numbers        | Review/clean field                      |

## Edge Cases

| Scenario                                        | Expected behavior         | Warning             |
| ----------------------------------------------- | ------------------------- | ------------------- |
| Email includes display-name text                | Treated as invalid format | INVALID_EMAIL       |
| Phone missing country code in international ops | Not guessed               | PHONE_NEEDS_COUNTRY |
| Phone too short/too long                        | Rejected                  | INVALID_PHONE       |
| Single-word name                                | Stored as first only      | MISSING_LAST        |
| Non-Latin characters                            | Preserved                 | none unless empty   |

## Testing

### Test Cases

| Category       | Samples to include                                                                                     |
| -------------- | ------------------------------------------------------------------------------------------------------ |
| Email          | valid, uppercase, extra spaces, missing @, missing TLD                                                 |
| Phone          | US 10-digit, US 11-digit starting with 1, international with +, too short, too long, punctuation-heavy |
| Names          | first/last present, full_name only, extra spaces, hyphenated, apostrophe, single token                 |
| Missing fields | email missing, phone missing, name missing, all missing                                                |

### Expected Results

| Requirement        | Pass criteria                                                   |
| ------------------ | --------------------------------------------------------------- |
| Consistency        | Same input always produces same normalized outputs and warnings |
| Safety             | Invalid email/phone never written as normalized values          |
| Workflow readiness | warnings[] reliably drives branching and review                 |
| Clean outputs      | Names remain human-readable and stable for personalization      |

### Optional Automation

| Automation              | Outcome                                                  |
| ----------------------- | -------------------------------------------------------- |
| Pre-write normalization | Prevents bad identity data from entering CRM             |
| Review queue            | Creates task/ticket when INVALID_EMAIL or INVALID_PHONE  |
| Enrichment step         | Routes PHONE_NEEDS_COUNTRY or MISSING_NAME to enrichment |
| Outbound block          | Stops sequences/SMS when normalized values are null      |
