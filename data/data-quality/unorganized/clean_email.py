"""
clean_email.py – Normalize email addresses with best practices.

Usage:
    python clean_email.py input.csv
    python clean_email.py input.csv ColumnName
    python clean_email.py input.csv ColumnName output.csv

Behavior:
    - Lowercase email
    - Remove invalid characters
    - Strip whitespace
    - Remove mailto:
    - Remove display names like "John Smith <email>"
    - Validate format
    - If no column provided → auto-detect columns containing "email"
    - Output: {input_stem}_cleaned.csv + clean_email_log.txt
"""

import sys
import re
from pathlib import Path
import pandas as pd


# ==========================================================
# Helpers
# ==========================================================

EMAIL_REGEX = re.compile(
    r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$"
)


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


def extract_email(text: str) -> str:
    """Extract and normalize a clean email address."""
    if pd.isna(text):
        return ""

    s = str(text).strip()

    if s == "":
        return ""

    # Remove mailto:
    if s.lower().startswith("mailto:"):
        s = s[7:]

    # Extract email from display names: "John Smith <email>"
    match = re.search(r"<([^>]+)>", s)
    if match:
        s = match.group(1).strip()

    # Remove illegal characters
    s = s.replace(" ", "").replace(";", "").replace(",", "")

    # Lowercase (best practice)
    s = s.lower()

    # Basic email validation
    if EMAIL_REGEX.match(s):
        return s

    return ""


def detect_email_columns(df: pd.DataFrame):
    """Detect columns containing 'email'."""
    return [c for c in df.columns if "email" in c.lower()]


def write_log(log_path, columns_cleaned, changes):
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("CLEAN EMAIL LOG\n")
        f.write("===============\n\n")

        f.write("Columns cleaned:\n")
        for c in columns_cleaned:
            f.write(f"  - {c}\n")

        f.write("\nChanged values:\n")
        f.write("--------------------------\n")

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
            cleaned = extract_email(val)
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
        print("  python clean_email.py input.csv")
        print("  python clean_email.py input.csv ColumnName")
        print("  python clean_email.py input.csv ColumnName output.csv")
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    # Parse columns and optional output
    columns = []
    output_path = None

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.endswith(".csv"):
            output_path = Path(arg).resolve()
            break
        columns.append(arg)
        i += 1

    df = read_csv_with_fallback(input_path)

    # Auto-detect if no columns provided
    if not columns:
        columns = detect_email_columns(df)
        if not columns:
            raise ValueError("No email columns found and none provided.")

    # Default output
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_cleaned{input_path.suffix}")

    log_path = input_path.with_name("clean_email_log.txt")

    cleaned_df, changes = clean_dataframe(df, columns)
    cleaned_df.to_csv(output_path, index=False)
    write_log(log_path, columns, changes)

    print(f"Cleaned CSV saved to: {output_path}")
    print(f"Log saved to:        {log_path}")


if __name__ == "__main__":
    main()
