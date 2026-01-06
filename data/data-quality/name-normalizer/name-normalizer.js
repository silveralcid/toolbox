/*
  Name Normalizer (Vanilla JS)
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
    first: "first",
    last: "last",
    full_name: "full_name",
  },

  OUTPUT_FIELDS: {
    first: "first_norm",
    last: "last_norm",
    full_name: "full_name_norm",
  },

  DEFAULTS: {
    PREFER_SPLIT_FIELDS: true,
    DERIVE_FULL_NAME: true,
    SPLIT_FULL_NAME: true,
    APPLY_SAFE_TITLECASE: true,

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

function normalizeTokenCase(tok) {
  if (!tok) return tok;

  if (/^(I|II|III|IV|V|VI|VII|VIII|IX|X)$/i.test(tok)) return tok.toUpperCase();
  if (/^(jr|sr)$/i.test(tok)) return tok[0].toUpperCase() + tok.slice(1).toLowerCase();

  const isAllLower = tok === tok.toLowerCase();
  const isAllUpper = tok === tok.toUpperCase();
  if (isAllLower || isAllUpper) return tok.charAt(0).toUpperCase() + tok.slice(1).toLowerCase();

  return tok;
}

function cleanNameValue(raw, opts, warnings) {
  if (raw === undefined || raw === null) return null;

  if (typeof raw !== "string") {
    if (opts.COERCE_NON_STRING) raw = String(raw);
    else {
      warnings.push("VALUE_NOT_STRING");
      return raw;
    }
  }

  let s = raw;

  const before = s;
  s = s.replace(/^[\s"'`.,;:(){}\[\]<>_=-]+/, "").replace(/[\s"'`.,;:(){}\[\]<>_=-]+$/, "");
  if (s !== before) warnings.push("STRIPPED_EDGE_PUNCT");

  s = s.trim();
  if (!s) return null;

  if (opts.APPLY_SAFE_TITLECASE) {
    s = s
      .split(" ")
      .filter(Boolean)
      .map((t) => t.split("-").map((p) => normalizeTokenCase(p)).join("-"))
      .join(" ");
  }

  return s || null;
}

function buildFullName(first, last) {
  const parts = [];
  if (first) parts.push(first);
  if (last) parts.push(last);
  return parts.length ? parts.join(" ") : null;
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

  const fm = isPlainObject(CONFIG.FIELD_MAP) ? CONFIG.FIELD_MAP : {};
  const of = isPlainObject(CONFIG.OUTPUT_FIELDS) ? CONFIG.OUTPUT_FIELDS : {
    first: "first",
    last: "last",
    full_name: "full_name",
  };

  const rawFirst = fm.first ? getByPath(sourceObj, fm.first) : { found: false, value: null };
  const rawLast = fm.last ? getByPath(sourceObj, fm.last) : { found: false, value: null };
  const rawFull = fm.full_name ? getByPath(sourceObj, fm.full_name) : { found: false, value: null };

  if (opts.EMIT_WARNINGS) {
    if (fm.first && !rawFirst.found) warnings.push("FIELD_MISSING");
    if (fm.last && !rawLast.found) warnings.push("FIELD_MISSING");
    if (fm.full_name && !rawFull.found) warnings.push("FIELD_MISSING");
  }

  const firstWarnings = [];
  const lastWarnings = [];
  const fullWarnings = [];

  let first = rawFirst.found ? cleanNameValue(rawFirst.value, opts, firstWarnings) : null;
  let last = rawLast.found ? cleanNameValue(rawLast.value, opts, lastWarnings) : null;
  let full_name = rawFull.found ? cleanNameValue(rawFull.value, opts, fullWarnings) : null;

  const hasSplit = !!(first || last);

  if (opts.PREFER_SPLIT_FIELDS && hasSplit) {
    if (opts.DERIVE_FULL_NAME && !full_name) {
      full_name = buildFullName(first, last);
      if (full_name) warnings.push("BUILT_FULL_NAME");
    }
  } else if (opts.SPLIT_FULL_NAME && full_name && (!first || !last)) {
    const parts = full_name.split(" ").filter(Boolean);
    if (!first && parts.length >= 1) first = parts[0];
    if (!last) {
      if (parts.length >= 2) last = parts.slice(1).join(" ");
      else warnings.push("MISSING_LAST");
    }
    warnings.push("USED_FULL_NAME_SPLIT");
  } else if (opts.DERIVE_FULL_NAME && !full_name && (first || last)) {
    full_name = buildFullName(first, last);
    if (full_name) warnings.push("BUILT_FULL_NAME");
  }

  if (!first && !last && !full_name) warnings.push("MISSING_NAME");

  const outputs = {
    [of.first]: first,
    [of.last]: last,
    [of.full_name]: full_name,
  };

  for (const [k, v] of Object.entries(outputs)) {
    const before = sourceObj[k];
    const beforeComparable = typeof before === "string" ? before : JSON.stringify(before);
    const afterComparable = typeof v === "string" ? v : JSON.stringify(v);
    if (beforeComparable !== afterComparable) changed.push(k);
  }

  if (opts.EMIT_CHANGED_FIELDS) outputs.name_changed_fields = Array.from(new Set(changed));
  if (opts.EMIT_WARNINGS) outputs.name_warnings = Array.from(new Set([
    ...warnings,
    ...firstWarnings,
    ...lastWarnings,
    ...fullWarnings,
  ]));

  return outputs;
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
