"""
clean_linkedin.py – Normalize LinkedIn URLs and validate proper structure.

Usage:
    python clean_linkedin.py input.csv
    python clean_linkedin.py input.csv ColumnName
    python clean_linkedin.py input.csv ColumnName output.csv

Rules:
    - Keep only LinkedIn links
    - Must contain one of:
        /in/, /company/, /school/, /showcase/, /groups/
    - Remove http/https
    - Keep www.
    - Lowercase domain
    - Remove trailing slash
    - Output: {input_stem}_cleaned.csv + clean_linkedin_log.txt
"""

import sys
import re
from pathlib import Path
import pandas as pd
from urllib.parse import urlparse


# ==========================================================
# Helpers
# ==========================================================

VALID_LINKEDIN_PATHS = [
    "/in/",
    "/company/",
    "/school/",
    "/showcase/",
    "/groups/",
]


def read_csv_with_fallback(path: Path) -> pd.DataFrame:
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            print(f"Loaded CSV using encoding: {enc}")
            return df
        except Exception:
            continue
    raise RuntimeError("Could not decode CSV.")


def normalize_linkedin_url(value: str) -> str:
    """Normalize and validate LinkedIn URLs."""
    if pd.isna(value):
        return ""

    v = str(value).strip()
    if v == "":
        return ""

    v = v.replace(" ", "")

    # Ensure scheme for parsing
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+\-.]*://", v):
        v_for_parse = "https://" + v
    else:
        v_for_parse = v

    try:
        parsed = urlparse(v_for_parse)
        domain = parsed.netloc.lower()
        path = parsed.path.rstrip("/")

        # Keep only linkedin domains
        if not ("linkedin.com" in domain):
            return ""   # delete if not linkedin

        # Ensure www. exists
        if not domain.startswith("www."):
            domain = "www." + domain

        # Must include valid LinkedIn path types
        valid = False
        p = path.lower() + "/"  # make sure last slash is handled
        for rule in VALID_LINKEDIN_PATHS:
            if rule in p:
                valid = True
                break

        if not valid:
            return ""  # delete if not an allowed LinkedIn type

        # Reassemble
        cleaned = domain + path
        cleaned = re.sub(r"//+", "/", cleaned)

        return cleaned

    except Exception:
        return ""


def detect_linkedin_columns(df: pd.DataFrame):
    """Auto-detect columns containing 'linkedin' or 'lnkd'."""
    return [
        c for c in df.columns
        if "linkedin" in c.lower() or "lnkd" in c.lower()
    ]


def write_log(log_path, columns_cleaned, changes):
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("CLEAN LINKEDIN LOG\n")
        f.write("===================\n\n")

        f.write("Columns cleaned:\n")
        for c in columns_cleaned:
            f.write(f"  - {c}\n")

        f.write("\nChanged values:\n")
        f.write("-------------------------\n")
        if not changes:
            f.write("No values changed.\n")
        else:
            for old, new, col in changes:
                f.write(f"[{col}] {old} → {new}\n")


# ==========================================================
# Cleaning
# ==========================================================

def clean_dataframe(df, columns):
    changes = []

    for col in columns:
        def clean_cell(val):
            cleaned = normalize_linkedin_url(val)
            if str(val).strip() != cleaned:
                changes.append((str(val), cleaned, col))
            return cleaned

        df[col] = df[col].apply(clean_cell)

    return df, changes


# ==========================================================
# Entrypoint
# ==========================================================

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python clean_linkedin.py input.csv")
        print("  python clean_linkedin.py input.csv ColumnName")
        print("  python clean_linkedin.py input.csv ColumnName output.csv")
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    columns = []
    output_path = None

    # Parse columns and/or output
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.endswith(".csv"):
            output_path = Path(arg).resolve()
            break
        columns.append(arg)
        i += 1

    df = read_csv_with_fallback(input_path)

    # Auto-detect LinkedIn columns
    if not columns:
        columns = detect_linkedin_columns(df)
        if not columns:
            raise ValueError("No LinkedIn columns found and none provided.")

    # Default output
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_cleaned{input_path.suffix}")

    log_path = input_path.with_name("clean_linkedin_log.txt")

    cleaned_df, changes = clean_dataframe(df, columns)
    cleaned_df.to_csv(output_path, index=False)
    write_log(log_path, columns, changes)

    print(f"Cleaned LinkedIn CSV saved to: {output_path}")
    print(f"Log saved to:                 {log_path}")


if __name__ == "__main__":
    main()
