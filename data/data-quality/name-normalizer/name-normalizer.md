# Name Normalizer

## Problem It Solves

Standardizes person name fields into consistent `first`, `last`, and `full_name` outputs for matching, dedupe, routing, and personalization. Supports both input styles: combined full name and separate first/last fields.

## Best Use Cases

### Use Case #1

Normalize name fields before writing to CRM to keep contact records clean and consistent.

### Use Case #2

Create reliable personalization fields for outbound (email/SMS templates, AI agents).

### Use Case #3

Pre-dedupe cleanup so “same person” matching is less error-prone when emails/phones are missing.

## Inputs

### Schema

Assumes Whitespace Cleaner runs before this script, so values are trimmed, spacing is sane, and invisible characters are removed.

| Config item   | Type   | Meaning                                             |
| ------------- | ------ | --------------------------------------------------- |
| FIELD_MAP     | object | Input field paths for `first`, `last`, `full_name`  |
| OUTPUT_FIELDS | object | Output field names for `first`, `last`, `full_name` |
| DEFAULTS      | object | Behavior controls (casing, splitting, derivation)   |

## Outputs

### Schema

Returns the original record merged with normalized name fields by default.

| Field                  | Type          | Notes                                                  |
| ---------------------- | ------------- | ------------------------------------------------------ |
| first (output key)     | string | null | Cleaned or derived first name                          |
| last (output key)      | string | null | Cleaned or derived last name                           |
| full_name (output key) | string | null | Cleaned or derived full name                           |
| name_warnings          | string[]      | Optional flags (only when enabled)                     |
| name_changed_fields    | string[]      | Optional list of keys that changed (only when enabled) |

## Operator Guide

### Config you edit at the top

| Setting              | Recommended default | Purpose                                                                |
| -------------------- | ------------------- | ---------------------------------------------------------------------- |
| OUTPUT_MODE          | `merge`             | `merge` adds outputs onto original object, `only` returns only outputs |
| PREFER_SPLIT_FIELDS  | `true`              | If first/last exist, treat them as authoritative over full_name        |
| DERIVE_FULL_NAME     | `true`              | Build full_name from first/last when missing                           |
| SPLIT_FULL_NAME      | `true`              | Derive first/last from full_name when missing                          |
| APPLY_SAFE_TITLECASE | `true`              | Best-effort casing normalization that avoids mangling mixed-case       |
| EMIT_CHANGED_FIELDS  | `true`              | Returns `name_changed_fields`                                          |
| EMIT_WARNINGS        | `true`              | Returns `name_warnings`                                                |
| COERCE_NON_STRING    | `false`             | If true, converts non-string values to strings before processing       |

### FIELD_MAP inputs

This determines where the script reads name inputs from your payload.

| Input source              | FIELD_MAP example                                                                                  |
| ------------------------- | -------------------------------------------------------------------------------------------------- |
| Standard top-level fields | `{ first: "first", last: "last", full_name: "full_name" }`                                         |
| Nested CRM payload        | `{ first: "properties.firstname", last: "properties.lastname", full_name: "properties.fullname" }` |
| Only full name available  | `{ full_name: "name", first: "", last: "" }`                                                       |

### OUTPUT_FIELDS

This determines where the script writes normalized outputs.

| Goal                       | OUTPUT_FIELDS example                                                     |
| -------------------------- | ------------------------------------------------------------------------- |
| Overwrite existing fields  | `{ first: "first", last: "last", full_name: "full_name" }`                |
| Write into separate fields | `{ first: "first_norm", last: "last_norm", full_name: "full_name_norm" }` |

### Minimal steps (Zapier and n8n)

| Step | Action                                                 | Outcome                                   |
| ---- | ------------------------------------------------------ | ----------------------------------------- |
| 1    | Run Whitespace Cleaner first on your name fields       | Removes stray spacing and invisible chars |
| 2    | Place this Name Normalizer next                        | Normalizes/derives first/last/full_name   |
| 3    | Write normalized outputs back to CRM or use downstream | Consistent personalization fields         |
| 4    | Branch on warnings                                     | Optional review/enrichment paths          |

## Logic Reference

### Normalization rules

| Rule                         | What it does                                       | Example                                        |
| ---------------------------- | -------------------------------------------------- | ---------------------------------------------- |
| Strip edge punctuation       | Removes surrounding quotes/commas/extra separators | `"  ,Bob  "` → `Bob`                           |
| Safe title-casing (optional) | Titlecases tokens only when all-lower or all-upper | `SMITH` → `Smith`, `McDonald` stays `McDonald` |
| Preserve hyphens/apostrophes | Keeps legitimate name punctuation                  | `Anne-Marie`, `O'Neil` preserved               |
| Prefer split fields          | If first/last provided, they win over full_name    | Avoids bad splitting                           |
| Derive full_name             | full_name becomes “first last” when missing        | `Bob` + `Smith` → `Bob Smith`                  |
| Split full_name              | If first/last missing, split full_name best-effort | `Bob A Smith` → first=`Bob`, last=`A Smith`    |
| Single token split           | If full_name is one token, set first only          | `Madonna` → first=`Madonna`, last=null         |

### Warnings (optional)

| Warning              | When it happens                                      |
| -------------------- | ---------------------------------------------------- |
| FIELD_MISSING        | A mapped input path is not found                     |
| VALUE_NOT_STRING     | Input exists but is not a string and coercion is off |
| MISSING_NAME         | No usable first/last/full_name present               |
| MISSING_LAST         | full_name has only one token                         |
| USED_FULL_NAME_SPLIT | first/last derived by splitting full_name            |
| BUILT_FULL_NAME      | full_name derived from first/last                    |
| STRIPPED_EDGE_PUNCT  | Edge punctuation removed from a name value           |

## Edge Cases

| Scenario                            | Expected behavior                             |
| ----------------------------------- | --------------------------------------------- |
| Suffixes like Jr/Sr/III             | Safe titlecase keeps common forms readable    |
| Multi-part last names               | Split assigns remainder to last (best-effort) |
| Hyphenated first or last            | Preserved                                     |
| All-caps input                      | Normalized to titlecase per token             |
| Mixed-case (McDonald, iPhone-style) | Preserved, not forced into titlecase          |

## Testing

### Test Cases

| Input                                 | Expected output                                   |
| ------------------------------------- | ------------------------------------------------- |
| first=`"  BOB "`, last=`" SMITH"`     | first=`Bob`, last=`Smith`, full_name=`Bob Smith`  |
| full_name=`"bob a smith"`             | first=`Bob`, last=`A Smith`, USED_FULL_NAME_SPLIT |
| full_name=`"madonna"`                 | first=`Madonna`, last=null, MISSING_LAST          |
| first=`"Anne-Marie"`, last=`"O'NEIL"` | first=`Anne-Marie`, last=`O'Neil`                 |
| missing all                           | MISSING_NAME                                      |

### Optional Automation

| Automation              | Outcome                                               |
| ----------------------- | ----------------------------------------------------- |
| Pre-write normalization | Keeps CRM name fields clean                           |
| Personalization safety  | Ensures first/full_name are usable before outbound    |
| Review queue            | Flags MISSING_NAME or suspicious patterns for cleanup |