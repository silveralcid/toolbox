/*
  Whitespace Cleaner (Vanilla JS)
  One script for Zapier Code step + n8n Code node.

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
    // Examples:
    // full_name: "full_name",
    // company_clean: "company",
    // note_clean: "properties.note",
  },

  DEFAULTS: {
    EMPTY_TO_NULL: true,
    TRIM_EDGES: true,
    COLLAPSE_SPACES: true,
    NORMALIZE_NEWLINES: "lf", // "lf" | "none"
    COLLAPSE_BLANK_LINES: false,
    REMOVE_ZERO_WIDTH: true,

    EMIT_CHANGED_FIELDS: true,
    EMIT_WARNINGS: true,

    // If true, non-string values are converted via String(value) and cleaned.
    // If false, non-string values are left as-is and flagged.
    COERCE_NON_STRING: false,
  },
};

/* =========================
   HELPERS
   ========================= */
function isPlainObject(v) {
  return v && typeof v === "object" && !Array.isArray(v);
}

function toNullIfEmptyString(s) {
  return s === "" ? null : s;
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

function cleanWhitespace(raw, opts, warnings) {
  if (raw === undefined || raw === null) return null;

  if (typeof raw !== "string") {
    if (opts.COERCE_NON_STRING) raw = String(raw);
    else {
      warnings.push("VALUE_NOT_STRING");
      return raw;
    }
  }

  let s = raw;

  if (opts.REMOVE_ZERO_WIDTH) {
    s = s.replace(/[\u200B-\u200D\uFEFF]/g, "");
  }

  if (opts.NORMALIZE_NEWLINES === "lf") {
    s = s.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  }

  if (opts.TRIM_EDGES) {
    s = s.trim();
  }

  if (opts.COLLAPSE_SPACES) {
    // Collapse internal spaces/tabs while preserving newlines
    s = s
      .split("\n")
      .map((line) => line.replace(/[ \t\f\v]+/g, " ").trimEnd())
      .join("\n");
  }

  if (opts.COLLAPSE_BLANK_LINES) {
    s = s.replace(/\n{3,}/g, "\n\n");
  }

  if (opts.EMPTY_TO_NULL) {
    s = toNullIfEmptyString(s);
    if (s === null) warnings.push("CLEANED_TO_EMPTY");
  }

  return s;
}

function buildOutput(original, cleanedObj) {
  if (CONFIG.OUTPUT_MODE === "only") return cleanedObj;
  return { ...original, ...cleanedObj };
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
      out[outKey] = opts.EMPTY_TO_NULL ? null : null;
      continue;
    }

    const before = value;
    const fieldWarnings = [];
    const after = cleanWhitespace(before, opts, fieldWarnings);

    out[outKey] = after;

    const beforeComparable = typeof before === "string" ? before : JSON.stringify(before);
    const afterComparable = typeof after === "string" ? after : JSON.stringify(after);
    if (beforeComparable !== afterComparable) changed.push(outKey);

    if (opts.EMIT_WARNINGS && fieldWarnings.length) warnings.push(...fieldWarnings);
  }

  if (opts.EMIT_CHANGED_FIELDS) out.whitespace_changed_fields = Array.from(new Set(changed));
  if (opts.EMIT_WARNINGS) out.whitespace_warnings = Array.from(new Set(warnings));

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
    const cleaned = processRecord(original);
    return { json: buildOutput(original, cleaned) };
  });
}

if (isN8nSingleItemRuntime()) {
  const original = $json || {};
  const cleaned = processRecord(original);
  return { json: buildOutput(original, cleaned) };
}

if (isZapierRuntime()) {
  const original = inputData || {};
  const cleaned = processRecord(original);
  return buildOutput(original, cleaned);
}

throw new Error("Unsupported runtime: expected Zapier inputData or n8n $input/$json.");
