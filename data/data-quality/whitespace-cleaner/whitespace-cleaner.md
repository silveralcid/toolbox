# Whitespace Cleaner

## Problem It Solves

Cleans messy text fields by trimming edges and normalizing internal whitespace so downstream matching, routing, personalization, and data storage behave consistently.

## Best Use Cases

### Use Case #1

Pre-write cleanup before updating CRM fields (names, titles, notes, form inputs).

### Use Case #2

Prepare strings for matching/dedupe (company name, domain, email subject lines, identifiers).

### Use Case #3

Improve message formatting before sending email/SMS/Slack (remove accidental double spaces, stray newlines).

## Inputs

### Schema

This script reads a source object (Zapier `inputData` or n8n `item.json`) and extracts only the fields you configure.

| Config item | Type   | Meaning                                           |
| ----------- | ------ | ------------------------------------------------- |
| FIELD_MAP   | object | Output key → input path (dot paths supported)     |
| DEFAULTS    | object | Behavior controls (trim, collapse, newline rules) |

## Outputs

### Schema

Returns the original record merged with cleaned fields by default.

| Field                     | Type          | Notes                                                         |
| ------------------------- | ------------- | ------------------------------------------------------------- |
| (mapped output keys)      | string | null | Cleaned values for each configured field                      |
| whitespace_warnings       | string[]      | Optional flags (only when enabled)                            |
| whitespace_changed_fields | string[]      | Optional list of output keys that changed (only when enabled) |

## Operator Guide

### Config you edit at the top

| Setting              | Recommended default | Purpose                                                                                   |
| -------------------- | ------------------- | ----------------------------------------------------------------------------------------- |
| OUTPUT_MODE          | `merge`             | `merge` adds cleaned fields onto the original object, `only` returns only cleaned outputs |
| EMPTY_TO_NULL        | `true`              | Converts empty strings after cleaning to null                                             |
| TRIM_EDGES           | `true`              | Removes leading/trailing whitespace                                                       |
| COLLAPSE_SPACES      | `true`              | Collapses repeated spaces/tabs inside text to single spaces                               |
| NORMALIZE_NEWLINES   | `lf`                | Converts CRLF/CR to LF for consistency                                                    |
| COLLAPSE_BLANK_LINES | `false`             | Optional; reduces multiple blank lines to a single blank line                             |
| REMOVE_ZERO_WIDTH    | `true`              | Removes zero-width characters that cause invisible formatting issues                      |
| EMIT_CHANGED_FIELDS  | `true`              | Returns `whitespace_changed_fields`                                                       |
| EMIT_WARNINGS        | `true`              | Returns `whitespace_warnings`                                                             |

### FIELD_MAP patterns

| Pattern                  | Example                                                | Result                                  |
| ------------------------ | ------------------------------------------------------ | --------------------------------------- |
| Simple top-level fields  | `{ full_name_clean: "full_name" }`                     | Writes `full_name_clean`                |
| Nested input paths       | `{ note_clean: "properties.note" }`                    | Reads nested value safely               |
| Overwrite existing field | `{ full_name: "full_name" }`                           | Replaces `full_name` with cleaned value |
| Multiple fields at once  | `{ first: "first", last: "last", company: "company" }` | Cleans all mapped fields                |

### Minimal steps (Zapier and n8n)

| Step | Action                                                  | Outcome                                |
| ---- | ------------------------------------------------------- | -------------------------------------- |
| 1    | Place the Code step/node immediately after your trigger | Cleans data before writeback/routing   |
| 2    | Set FIELD_MAP to match your incoming fields             | Script knows what to clean             |
| 3    | Use cleaned outputs in downstream steps                 | Consistent strings everywhere          |
| 4    | Optionally branch on changed fields/warnings            | Review or special handling when needed |

## Logic Reference

### Cleaning rules applied per field

| Rule                            | What it does                                                            | Example                     |
| ------------------------------- | ----------------------------------------------------------------------- | --------------------------- |
| Remove zero-width               | Removes characters like ZWSP that break formatting                      | `"A\u200Blice"` → `"Alice"` |
| Normalize newlines              | Converts CRLF/CR to LF                                                  | `"\r\n"` → `"\n"`           |
| Trim edges                      | Removes leading/trailing whitespace                                     | `"  hello  "` → `"hello"`   |
| Collapse spaces                 | Converts runs of whitespace (spaces/tabs) inside lines to single spaces | `"a   b\t\tc"` → `"a b c"`  |
| Collapse blank lines (optional) | Reduces multiple blank lines                                            | `"a\n\n\nb"` → `"a\n\nb"`   |
| Empty to null (optional)        | Converts `""` to `null` after cleaning                                  | `"   "` → `null`            |

### Warnings (optional)

| Warning          | When it happens                                                                            |
| ---------------- | ------------------------------------------------------------------------------------------ |
| VALUE_NOT_STRING | Field exists but is not a string (number/object/array); script stringifies only if enabled |
| FIELD_MISSING    | Mapped input path not found                                                                |
| CLEANED_TO_EMPTY | Cleaning produced empty/null output                                                        |

## Edge Cases

| Scenario                                | Expected behavior                                                   |
| --------------------------------------- | ------------------------------------------------------------------- |
| Field is missing                        | Output becomes null only if you choose to emit it; warning optional |
| Field is all whitespace                 | Output becomes null if EMPTY_TO_NULL is true                        |
| Field includes tabs and multiple spaces | Collapses to single spaces when COLLAPSE_SPACES is true             |
| Field includes Windows newlines         | Normalizes to `\n` when NORMALIZE_NEWLINES is `lf`                  |
| Field includes invisible characters     | Removed when REMOVE_ZERO_WIDTH is true                              |

## Testing

### Test Cases

| Input                       | Config               | Expected output           |
| --------------------------- | -------------------- | ------------------------- |
| `"  Acme   Inc "`           | trim + collapse      | `"Acme Inc"`              |
| `"Line1\r\nLine2\rLine3\n"` | normalize newlines   | `"Line1\nLine2\nLine3\n"` |
| `"A\u200Blice"`             | remove zero-width    | `"Alice"`                 |
| `"   "`                     | empty_to_null        | `null`                    |
| `"a\n\n\nb"`                | collapse blank lines | `"a\n\nb"`                |

### Optional Automation

| Automation                 | Outcome                                           |
| -------------------------- | ------------------------------------------------- |
| Pre-write normalization    | Prevents messy text from entering CRM             |
| Review on changed fields   | Flags records where critical fields were modified |
| Standardize notes/messages | More readable internal logs and outbound content  |
