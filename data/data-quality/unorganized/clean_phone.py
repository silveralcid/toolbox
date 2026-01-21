"""
clean_phone.py – Clean phone numbers for specified or auto-detected columns.

Usage:
    python clean_phone.py input.csv
    python clean_phone.py input.csv PhoneColumn
    python clean_phone.py input.csv Phone1 Phone2 output.csv

If no columns provided:
    Automatically clean any columns whose names contain:
    "phone", "cell phone", "mobile", "home phone", "work phone", etc.

Output:
    {input_stem}_cleaned.csv
    clean_phone_log.txt
"""

import sys
import re
from pathlib import Path
import pandas as pd
import phonenumbers


# Regex to detect phone-ish content
PHONE_LIKE_REGEX = re.compile(r"""
    (?<!\d)
    (\+?\d[\d\-\.\(\)\s]{6,20}\d)
    (?!\d)
""", re.VERBOSE)


# ============================================================
# Phone cleaning internals
# ============================================================

def normalize_raw_digits(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("+"):
        return "+" + re.sub(r"\D", "", raw[1:])
    return re.sub(r"\D", "", raw)


def normalize_to_e164(raw: str):
    if not raw:
        return raw

    digits = normalize_raw_digits(raw)

    if digits.startswith("+"):
        try:
            parsed = phonenumbers.parse(digits)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            return digits
        except Exception:
            return digits

    assumed = "+1" + digits
    try:
        parsed = phonenumbers.parse(assumed)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        return assumed
    except Exception:
        return assumed


def extract_and_clean_phone(value: str):
    if pd.isna(value):
        return value

    text = str(value).strip()
    if text == "":
        return text

    match = PHONE_LIKE_REGEX.search(text)
    if not match:
        return value

    candidate = match.group(1)
    return normalize_to_e164(candidate)


# ============================================================
# Auto-detection of phone-related columns
# ============================================================

PHONE_KEYWORDS = [
    "phone",
    "phone number",
    "cell",
    "cellphone",
    "cell phone",
    "mobile",
    "mobile phone",
    "work phone",
    "home phone",
    "business phone",
]


def detect_phone_columns(df: pd.DataFrame):
    cols = []
    for col in df.columns:
        cname = col.lower()
        for kw in PHONE_KEYWORDS:
            if kw in cname:
                cols.append(col)
                break
    return cols


# ============================================================
# CSV loading
# ============================================================

def read_csv_with_fallback(path: Path) -> pd.DataFrame:
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin1"]
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            print(f"Loaded using encoding: {enc}")
            return df
        except Exception:
            continue
    raise RuntimeError("Could not decode CSV.")


# ============================================================
# Logging
# ============================================================

def write_log(log_path, cleaned_columns, changes):
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("CLEAN PHONE LOG\n")
        f.write("================\n\n")

        f.write("Columns cleaned:\n")
        for c in cleaned_columns:
            f.write(f"  - {c}\n")

        f.write(f"\nTotal changed values: {len(changes)}\n\n")

        f.write("Changed entries:\n")
        f.write("----------------\n")
        if not changes:
            f.write("No values changed.\n")
        else:
            for old, new, col in changes:
                f.write(f"[{col}] {old} → {new}\n")


# ============================================================
# Cleaning wrapper
# ============================================================

def clean_dataframe(df: pd.DataFrame, columns):
    changes = []

    for col in columns:
        def clean_cell(val):
            cleaned = extract_and_clean_phone(val)
            if str(val).strip() != cleaned:
                changes.append((str(val), cleaned, col))
            return cleaned

        df[col] = df[col].apply(clean_cell)

    return df, changes


# ============================================================
# Entrypoint
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python clean_phone.py input.csv")
        print("  python clean_phone.py input.csv PhoneColumn")
        print("  python clean_phone.py input.csv Phone1 Phone2 output.csv")
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    columns = []
    output_path = None

    # Parse arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.endswith(".csv"):
            output_path = Path(arg).resolve()
            break
        columns.append(arg)
        i += 1

    df = read_csv_with_fallback(input_path)

    # Auto-detect columns if none provided
    if not columns:
        columns = detect_phone_columns(df)
        if not columns:
            raise ValueError("No phone-related columns found and none provided.")

    # Default output filename
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_cleaned{input_path.suffix}")

    # Log file
    log_path = input_path.with_name("clean_phone_log.txt")

    # Clean & save
    cleaned_df, changes = clean_dataframe(df, columns)
    cleaned_df.to_csv(output_path, index=False)
    write_log(log_path, columns, changes)

    print(f"Cleaned file saved to: {output_path}")
    print(f"Log saved to:         {log_path}")


if __name__ == "__main__":
    main()
