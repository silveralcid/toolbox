"""
clean_website.py – Normalize website URLs based on best practices (keeping www).

Usage:
    python clean_website.py input.csv
    python clean_website.py input.csv ColumnName
    python clean_website.py input.csv ColumnName output.csv

If no column is provided, any column with "website" or "url"
(case-insensitive) will be cleaned.

Output:
    {input_stem}_cleaned.csv
    clean_website_log.txt
"""

import sys
import re
from pathlib import Path
import pandas as pd
from urllib.parse import urlparse


# ==========================================================
# Helpers
# ==========================================================

def read_csv_with_fallback(path: Path) -> pd.DataFrame:
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin1"]
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            print(f"Loaded CSV using encoding: {enc}")
            return df
        except Exception:
            continue
    raise RuntimeError("Could not decode CSV.")


def normalize_url(value: str) -> str:
    """Clean a website URL AND ensure www. is present."""
    if pd.isna(value):
        return ""

    v = str(value).strip()
    if v == "":
        return ""

    # Remove spaces
    v = v.replace(" ", "")

    # Add scheme for parsing if missing
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+\-.]*://", v):
        v_for_parse = "https://" + v
    else:
        v_for_parse = v

    try:
        parsed = urlparse(v_for_parse)
        domain = parsed.netloc.lower()

        # Ensure domain always starts with www.
        if not domain.startswith("www."):
            domain = "www." + domain

        # Remove trailing slash in path
        path = parsed.path.rstrip("/")

        # Reassemble: www.domain/path
        cleaned = domain + path

        # Collapse double slashes inside path
        cleaned = re.sub(r"//+", "/", cleaned)

        return cleaned
    except Exception:
        return v



def detect_website_columns(df: pd.DataFrame):
    """Auto-detect columns containing website or url."""
    return [
        c for c in df.columns
        if "website" in c.lower() or "url" in c.lower()
    ]


def write_log(log_path, cleaned_cols, changes):
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("CLEAN WEBSITE LOG\n")
        f.write("=================\n\n")

        f.write("Columns cleaned:\n")
        for c in cleaned_cols:
            f.write(f"  - {c}\n")
        f.write("\n")

        f.write("Changed values:\n")
        f.write("------------------------------\n")

        if not changes:
            f.write("No values were changed.\n")
        else:
            for old, new, col in changes:
                f.write(f"[{col}] {old} → {new}\n")


# ==========================================================
# Cleaning
# ==========================================================

def clean_dataframe(df, columns):
    changes = []

    for col in columns:
        def apply_clean(val):
            cleaned = normalize_url(val)
            if str(val).strip() != cleaned:
                changes.append((str(val), cleaned, col))
            return cleaned

        df[col] = df[col].apply(apply_clean)

    return df, changes


# ==========================================================
# Entrypoint
# ==========================================================

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python clean_website.py input.csv")
        print("  python clean_website.py input.csv ColumnName")
        print("  python clean_website.py input.csv ColumnName output.csv")
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Cannot find file: {input_path}")

    columns = []
    output_path = None

    # Parse columns and/or output CSV
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.endswith(".csv"):
            output_path = Path(arg).resolve()
            break
        columns.append(arg)
        i += 1

    df = read_csv_with_fallback(input_path)

    # Auto-detect
    if not columns:
        columns = detect_website_columns(df)
        if not columns:
            raise ValueError("No website/url columns found and none provided.")

    # Default cleaned filename
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_cleaned{input_path.suffix}")

    # Log file
    log_path = input_path.with_name("clean_website_log.txt")

    # Run cleaning
    cleaned_df, changes = clean_dataframe(df, columns)

    cleaned_df.to_csv(output_path, index=False)
    write_log(log_path, columns, changes)

    print(f"Cleaned CSV saved to: {output_path}")
    print(f"Log file saved to:    {log_path}")


if __name__ == "__main__":
    main()
