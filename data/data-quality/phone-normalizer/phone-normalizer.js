/*
  Phone Normalizer (Vanilla JS)
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
    phone_norm: "phone",
    // mobile_norm: "mobile",
  },

  DEFAULTS: {
    DEFAULT_COUNTRY: "US",

    EMPTY_TO_NULL: true,
    ALLOW_MULTIPLE_SPLIT: true,
    STRIP_EXTENSION: true,

    VALIDATE_LENGTH: true,
    INFER_US_LOCAL: true,

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

function normalizePhoneValue(raw, opts, warnings) {
  if (raw === undefined || raw === null) return null;

  if (typeof raw !== "string") {
    if (opts.COERCE_NON_STRING) raw = String(raw);
    else {
      warnings.push("VALUE_NOT_STRING");
      return raw;
    }
  }

  let s = raw;

  if (opts.ALLOW_MULTIPLE_SPLIT) {
    const parts = s.split(/[;|,]/).map((x) => x.trim()).filter(Boolean);
    if (parts.length > 1) {
      warnings.push("MULTIPLE_PHONES_FOUND");
      s = parts[0];
    }
  }

  if (opts.STRIP_EXTENSION) {
    const extRe = /\s*(?:ext\.?|x)\s*\d+\s*$/i;
    if (extRe.test(s)) {
      warnings.push("PHONE_HAS_EXTENSION");
      s = s.replace(extRe, "").trim();
    }
  }

  if (s.startsWith("00")) s = "+" + s.slice(2);

  const hasPlus = s.startsWith("+");
  const digits = s.replace(/[^\d]/g, "");

  if (!digits) {
    warnings.push("INVALID_PHONE");
    return null;
  }

  if (hasPlus) {
    if (opts.VALIDATE_LENGTH && (digits.length < 8 || digits.length > 15)) {
      warnings.push("INVALID_PHONE");
      return null;
    }
    return "+" + digits;
  }

  const dc = String(opts.DEFAULT_COUNTRY || "US").toUpperCase();

  if (opts.INFER_US_LOCAL && dc === "US") {
    if (digits.length === 10) return "+1" + digits;
    if (digits.length === 11 && digits.startsWith("1")) return "+" + digits;
    warnings.push("INVALID_PHONE");
    return null;
  }

  warnings.push("PHONE_NEEDS_COUNTRY");
  return null;
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
    const after = normalizePhoneValue(before, opts, fieldWarnings);

    out[outKey] = after;

    const beforeComparable = typeof before === "string" ? before : JSON.stringify(before);
    const afterComparable = typeof after === "string" ? after : JSON.stringify(after);
    if (beforeComparable !== afterComparable) changed.push(outKey);

    if (opts.EMIT_WARNINGS && fieldWarnings.length) warnings.push(...fieldWarnings);
  }

  if (opts.EMIT_CHANGED_FIELDS) out.phone_changed_fields = Array.from(new Set(changed));
  if (opts.EMIT_WARNINGS) out.phone_warnings = Array.from(new Set(warnings));

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
