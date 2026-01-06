/*
  Unified Identity Normalizer (Vanilla JS)
*/

/* =========================
   CONFIG (EDIT THIS SECTION)
   ========================= */
const CONFIG = {
  DEFAULT_COUNTRY: "US",

  INPUT_MAP: {
    email: "email",
    phone: "phone",
    first: "first",
    last: "last",
    full_name: "full_name",
    default_country: "default_country",
  },

  OUTPUT_MODE: "merge", // "merge" | "only"
  WARNINGS_MODE: "dedupe", // "dedupe" | "all"
};

/* =========================
   HELPERS
   ========================= */
function toNullIfEmpty(v) {
  if (v === undefined || v === null) return null;
  const s = String(v).trim();
  return s.length ? s : null;
}

function getByPath(obj, path) {
  const p = toNullIfEmpty(path);
  if (!p) return null;
  const parts = p.split(".");
  let cur = obj;
  for (const k of parts) {
    if (cur && Object.prototype.hasOwnProperty.call(cur, k)) cur = cur[k];
    else return null;
  }
  return cur;
}

function collapseSpaces(s) {
  return s.replace(/\s+/g, " ").trim();
}

function stripEdgePunct(s) {
  return s
    .replace(/^[\s"'`.,;:(){}\[\]<>_=-]+/, "")
    .replace(/[\s"'`.,;:(){}\[\]<>_=-]+$/, "")
    .trim();
}

function safeTitleToken(tok) {
  if (!tok) return tok;
  if (/^(I|II|III|IV|V|VI|VII|VIII|IX|X)$/i.test(tok)) return tok.toUpperCase();
  if (/^(jr|sr)$/i.test(tok)) return tok[0].toUpperCase() + tok.slice(1).toLowerCase();
  const isAllLower = tok === tok.toLowerCase();
  const isAllUpper = tok === tok.toUpperCase();
  if (isAllLower || isAllUpper) return tok.charAt(0).toUpperCase() + tok.slice(1).toLowerCase();
  return tok;
}

function normalizeName(raw) {
  const v = toNullIfEmpty(raw);
  if (!v) return null;

  const cleaned = stripEdgePunct(collapseSpaces(v));
  if (!cleaned) return null;

  const tokens = cleaned.split(" ").map((t) =>
    t.split("-").map((p) => safeTitleToken(p)).join("-")
  );

  return tokens.join(" ");
}

function normalizeEmail(raw, warnings) {
  const v = toNullIfEmpty(raw);
  if (!v) return null;

  const candidate = v.toLowerCase();
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!re.test(candidate)) {
    warnings.push("INVALID_EMAIL");
    return null;
  }
  return candidate;
}

function normalizePhone(raw, defaultCountry, warnings) {
  let v = toNullIfEmpty(raw);
  if (!v) return null;

  const multiSplit = v.split(/[;|,]/).map((x) => x.trim()).filter(Boolean);
  if (multiSplit.length > 1) {
    warnings.push("MULTIPLE_PHONES_FOUND");
    v = multiSplit[0];
  }

  const extRe = /\s*(?:ext\.?|x)\s*\d+\s*$/i;
  if (extRe.test(v)) {
    warnings.push("PHONE_HAS_EXTENSION");
    v = v.replace(extRe, "").trim();
  }

  if (v.startsWith("00")) v = "+" + v.slice(2);

  const hasPlus = v.startsWith("+");
  const digits = v.replace(/[^\d]/g, "");
  if (!digits) {
    warnings.push("INVALID_PHONE");
    return null;
  }

  if (hasPlus) {
    if (digits.length < 8 || digits.length > 15) {
      warnings.push("INVALID_PHONE");
      return null;
    }
    return "+" + digits;
  }

  const dc = String(defaultCountry || CONFIG.DEFAULT_COUNTRY || "US").toUpperCase();

  if (dc === "US") {
    if (digits.length === 10) return "+1" + digits;
    if (digits.length === 11 && digits.startsWith("1")) return "+" + digits;
    warnings.push("INVALID_PHONE");
    return null;
  }

  warnings.push("PHONE_NEEDS_COUNTRY");
  return null;
}

function buildWarningsList(rawWarnings) {
  if (CONFIG.WARNINGS_MODE === "all") return rawWarnings;
  return Array.from(new Set(rawWarnings));
}

function normalizeRecord(sourceObj) {
  const raw = {
    email: getByPath(sourceObj, CONFIG.INPUT_MAP.email),
    phone: getByPath(sourceObj, CONFIG.INPUT_MAP.phone),
    first: getByPath(sourceObj, CONFIG.INPUT_MAP.first),
    last: getByPath(sourceObj, CONFIG.INPUT_MAP.last),
    full_name: getByPath(sourceObj, CONFIG.INPUT_MAP.full_name),
    default_country: getByPath(sourceObj, CONFIG.INPUT_MAP.default_country),
  };

  const warnings = [];

  let first = normalizeName(raw.first);
  let last = normalizeName(raw.last);
  let full_name = normalizeName(raw.full_name);

  if (!full_name && (first || last)) full_name = collapseSpaces([first, last].filter(Boolean).join(" "));

  if ((!first || !last) && full_name) {
    const parts = full_name.split(" ").filter(Boolean);
    if (!first && parts.length >= 1) first = parts[0];
    if (!last) {
      if (parts.length >= 2) last = parts.slice(1).join(" ");
      else warnings.push("MISSING_LAST");
    }
  }

  if (!first && !last && !full_name) warnings.push("MISSING_NAME");

  const email_norm = normalizeEmail(raw.email, warnings);
  const phone_norm = normalizePhone(raw.phone, raw.default_country || CONFIG.DEFAULT_COUNTRY, warnings);

  return {
    email_norm,
    phone_norm,
    first,
    last,
    full_name,
    warnings: buildWarningsList(warnings),
  };
}

/* =========================
   RUNTIME ADAPTER
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

function buildOutput(original, normalized) {
  if (CONFIG.OUTPUT_MODE === "only") return normalized;
  return { ...original, ...normalized };
}

/* =========================
   EXECUTION
   ========================= */
if (isN8nAllItemsRuntime()) {
  const items = $input.all();
  return items.map((item) => {
    const original = item.json || {};
    const normalized = normalizeRecord(original);
    return { json: buildOutput(original, normalized) };
  });
}

if (isN8nSingleItemRuntime()) {
  const original = $json || {};
  const normalized = normalizeRecord(original);
  return { json: buildOutput(original, normalized) };
}

if (isZapierRuntime()) {
  const original = inputData || {};
  const normalized = normalizeRecord(original);
  return buildOutput(original, normalized);
}

throw new Error("Unsupported runtime: expected Zapier inputData or n8n $input/$json.");