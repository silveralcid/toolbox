# Phone Normalizer

## Problem It Solves

Converts messy phone inputs into a consistent, matchable key for dedupe, routing, and SMS readiness. Flags invalid or ambiguous phones so workflows can branch instead of writing unreliable numbers.

## Best Use Cases

### Use Case #1

Pre-dedupe phone normalization before searching CRM for an existing contact/lead.

### Use Case #2

Inbound routing and ownership assignment using normalized phone keys.

### Use Case #3

Outbound readiness validation to block SMS when phone is invalid or missing country code.

## Inputs

### Schema

Assumes Whitespace Cleaner runs before this script, so values are already trimmed and stripped of invisible characters.

| Config item | Type   | Meaning                                                               |
| ----------- | ------ | --------------------------------------------------------------------- |
| FIELD_MAP   | object | Output key → input path (dot paths supported)                         |
| DEFAULTS    | object | Behavior controls (country inference, extension handling, validation) |

## Outputs

### Schema

Returns the original record merged with normalized phone fields by default.

| Field                | Type          | Notes                                                         |
| -------------------- | ------------- | ------------------------------------------------------------- |
| (mapped output keys) | string | null | Normalized phone in E.164-like format when possible           |
| phone_warnings       | string[]      | Optional flags (only when enabled)                            |
| phone_changed_fields | string[]      | Optional list of output keys that changed (only when enabled) |

## Operator Guide

### Config you edit at the top

| Setting              | Recommended default | Purpose                                                                          |                              |
| -------------------- | ------------------- | -------------------------------------------------------------------------------- | ---------------------------- |
| OUTPUT_MODE          | `merge`             | `merge` adds normalized fields onto original object, `only` returns only outputs |                              |
| DEFAULT_COUNTRY      | `US`                | Used only when input has no `+` country code                                     |                              |
| EMPTY_TO_NULL        | `true`              | Converts empty strings after normalization to null                               |                              |
| ALLOW_MULTIPLE_SPLIT | `true`              | Splits on `, ;                                                                   | ` and uses the first segment |
| STRIP_EXTENSION      | `true`              | Removes common extensions like `x123` or `ext 45`                                |                              |
| VALIDATE_LENGTH      | `true`              | Validates plausibility using digit length bounds                                 |                              |
| INFER_US_LOCAL       | `true`              | Enables US inference for 10-digit and 11-digit starting with 1                   |                              |
| EMIT_CHANGED_FIELDS  | `true`              | Returns `phone_changed_fields`                                                   |                              |
| EMIT_WARNINGS        | `true`              | Returns `phone_warnings`                                                         |                              |
| COERCE_NON_STRING    | `false`             | If true, converts non-string values to strings before processing                 |                              |

### FIELD_MAP patterns

| Pattern               | Example                                          | Result                                 |
| --------------------- | ------------------------------------------------ | -------------------------------------- |
| Simple top-level      | `{ phone_norm: "phone" }`                        | Writes `phone_norm`                    |
| Nested input path     | `{ phone_norm: "contact.phone" }`                | Reads nested safely                    |
| Overwrite existing    | `{ phone: "phone" }`                             | Replaces `phone` with normalized value |
| Multiple phone fields | `{ phone_norm: "phone", mobile_norm: "mobile" }` | Normalizes multiple fields             |

### Minimal steps (Zapier and n8n)

| Step | Action                                                   | Outcome                                  |
| ---- | -------------------------------------------------------- | ---------------------------------------- |
| 1    | Run Whitespace Cleaner first on your phone fields        | Removes stray spaces and invisible chars |
| 2    | Place this Phone Normalizer immediately after            | Produces consistent match key            |
| 3    | Write back normalized outputs to CRM or use for searches | Reliable dedupe and lookups              |
| 4    | Branch on warnings and null outputs                      | Review, enrichment, or block SMS         |

## Logic Reference

### Normalization rules applied per field

| Rule                             | What it does                                   | Example                             |
| -------------------------------- | ---------------------------------------------- | ----------------------------------- |
| Split multiple values (optional) | If multiple phones present, keep first segment | `"a, b"` → uses `a`                 |
| Strip extension (optional)       | Removes `x123` / `ext 45` suffix               | `"5551212 x9"` → `"5551212"`        |
| Convert `00` to `+`              | Treats `00` as international prefix            | `"0044..."` → `"+44..."`            |
| Keep digits                      | Removes non-digits, keeps optional leading `+` | `"(804) 555-1212"` → `"8045551212"` |
| International `+` format         | Accepts `+` then 8–15 digits                   | `"+442079460958"` remains           |
| US inference                     | 10 digits → +1, 11 digits starting with 1 → +  | `"8045551212"` → `"+18045551212"`   |
| Ambiguous local                  | If not US inference and no `+`, do not guess   | `"02079460958"` → null              |
| Empty to null                    | Converts `""` to null                          | `""` → null                         |

### Warnings (optional)

| Warning               | When it happens                                      |
| --------------------- | ---------------------------------------------------- |
| FIELD_MISSING         | Mapped input path not found                          |
| VALUE_NOT_STRING      | Field exists but is not a string and coercion is off |
| MULTIPLE_PHONES_FOUND | Multiple values detected and first segment used      |
| PHONE_HAS_EXTENSION   | Extension detected and stripped                      |
| INVALID_PHONE         | Fails plausibility checks                            |
| PHONE_NEEDS_COUNTRY   | No `+` and country cannot be inferred safely         |
| CLEANED_TO_EMPTY      | Normalization produced empty/null output             |

## Edge Cases

| Scenario                         | Expected behavior                            |
| -------------------------------- | -------------------------------------------- |
| International number without `+` | Not guessed; PHONE_NEEDS_COUNTRY             |
| Too short/too long               | INVALID_PHONE                                |
| Extension included               | Stripped if enabled; PHONE_HAS_EXTENSION     |
| Multiple numbers                 | First used if enabled; MULTIPLE_PHONES_FOUND |
| Non-string value                 | Warn or coerce based on config               |

## Testing

### Test Cases

| Input                           | Config    | Expected output                      |
| ------------------------------- | --------- | ------------------------------------ |
| `"(804) 555-1212"` + US default | infer US  | `+18045551212`                       |
| `"1-804-555-1212"` + US default | infer US  | `+18045551212`                       |
| `"+44 20 7946 0958"`            | intl      | `+442079460958`                      |
| `"0044 20 7946 0958"`           | 00→+      | `+442079460958`                      |
| `"804-555-1212 x45"`            | strip ext | `+18045551212` + PHONE_HAS_EXTENSION |
| `"020 7946 0958"` + US default  | no guess  | null + PHONE_NEEDS_COUNTRY           |

### Optional Automation

| Automation              | Outcome                                    |
| ----------------------- | ------------------------------------------ |
| Pre-write normalization | Prevents inconsistent phone formats in CRM |
| Review on invalid       | Creates task/ticket when INVALID_PHONE     |
| SMS block               | Stops SMS when normalized phone is null    |