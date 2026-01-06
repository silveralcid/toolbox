/*
  Email Normalizer (Vanilla JS)
  One script for Zapier Code step + n8n Code node.

  Assumes a Whitespace Cleaner step runs before this script.
  Zapier: uses inputData and returns an object
  n8n: processes $input.all() if available, otherwise $json
*/

/* =========================
   CONFIG (EDIT THIS SECTION)
   ========================= */
const CONFIG = {
  OUTPUT_MODE: "merge", // "merge" | "only"

  FIELD_MAP: {
    // outputKey: "input.path"
    email_norm: "email",
    // billing_email_norm: "billing.email",
  },

  DEFAULTS: {
    EMPTY_TO_NULL: true,
    LOWERCASE: true,
    EXTRACT_EMAIL: false,
    VALIDATE_FORMAT: true,

    EMIT_CHANGED_FIELDS: true,
    EMIT_WARNINGS: true,

    COERCE_NON_STRING: false,
  },
};

/* =========================
   HELPERS
   ========================= */
function isPlainObject(v) {
  return v && typeof v === "object" && !Array.isArray(v);
}

function toNullIfEmpty(v) {
  if (v === undefined || v === null) return null;
  const s = String(v);
  return s.length ? s : null;
}

function getByPath(obj, path) {
  if (!path || typeof path !== "string") return { found: false, value: null };
  const parts = path.split(".");
  let cur = obj;
  for (const k of parts) {
    if (cur && Object.prototype.hasOwnProperty.call(cur, k)) cur = cur[k];
    else return { found: false, value: null };
  }
  return { found: true, value: cur };
}

function normalizeEmailValue(raw, opts, warnings) {
  if (raw === undefined || raw === null) return null;

  if (typeof raw !== "string") {
    if (opts.COERCE_NON_STRING) raw = String(raw);
    else {
      warnings.push("VALUE_NOT_STRING");
      return raw;
    }
  }

  let s = raw;

  if (opts.EXTRACT_EMAIL) {
    const match = s.match(/[^\s<>"'(),;:]+@[^\s<>"'(),;:]+\.[^\s<>"'(),;:]+/);
    if (match && match[0] && match[0] !== s) {
      warnings.push("EMAIL_EXTRACTED");
      s = match[0];
    }
  }

  if (opts.LOWERCASE && typeof s === "string") {
    s = s.toLowerCase();
  }

  if (opts.VALIDATE_FORMAT && typeof s === "string") {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!re.test(s)) {
      warnings.push("INVALID_EMAIL");
      s = null;
    }
  }

  if (opts.EMPTY_TO_NULL && s === "") {
    warnings.push("CLEANED_TO_EMPTY");
    return null;
  }

  if (opts.EMPTY_TO_NULL && s === null) {
    warnings.push("CLEANED_TO_EMPTY");
    return null;
  }

  return s;
}

function buildOutput(original, outputs) {
  if (CONFIG.OUTPUT_MODE === "only") return outputs;
  return { ...original, ...outputs };
}

function processRecord(sourceObj) {
  const opts = CONFIG.DEFAULTS;
  const out = {};
  const warnings = [];
  const changed = [];

  const fieldMap = isPlainObject(CONFIG.FIELD_MAP) ? CONFIG.FIELD_MAP : {};

  for (const [outKey, inPath] of Object.entries(fieldMap)) {
    const { found, value } = getByPath(sourceObj, inPath);

    if (!found) {
      if (opts.EMIT_WARNINGS) warnings.push("FIELD_MISSING");
      out[outKey] = null;
      continue;
    }

    const before = value;
    const fieldWarnings = [];
    const after = normalizeEmailValue(before, opts, fieldWarnings);

    out[outKey] = after;

    const beforeComparable = typeof before === "string" ? before : JSON.stringify(before);
    const afterComparable = typeof after === "string" ? after : JSON.stringify(after);
    if (beforeComparable !== afterComparable) changed.push(outKey);

    if (opts.EMIT_WARNINGS && fieldWarnings.length) warnings.push(...fieldWarnings);
  }

  if (opts.EMIT_CHANGED_FIELDS) out.email_changed_fields = Array.from(new Set(changed));
  if (opts.EMIT_WARNINGS) out.email_warnings = Array.from(new Set(warnings));

  return out;
}

/* =========================
   RUNTIME DETECTION
   ========================= */
function isN8nAllItemsRuntime() {
  return typeof $input !== "undefined" && $input && typeof $input.all === "function";
}

function isN8nSingleItemRuntime() {
  return typeof $json !== "undefined" && $json;
}

function isZapierRuntime() {
  return typeof inputData !== "undefined" && inputData;
}

/* =========================
   EXECUTION
   ========================= */
if (isN8nAllItemsRuntime()) {
  const items = $input.all();
  return items.map((item) => {
    const original = item.json || {};
    const outputs = processRecord(original);
    return { json: buildOutput(original, outputs) };
  });
}

if (isN8nSingleItemRuntime()) {
  const original = $json || {};
  const outputs = processRecord(original);
  return { json: buildOutput(original, outputs) };
}

if (isZapierRuntime()) {
  const original = inputData || {};
  const outputs = processRecord(original);
  return buildOutput(original, outputs);
}

throw new Error("Unsupported runtime: expected Zapier inputData or n8n $input/$json.");
