"""
ZIP code cleaning script for ONE specific column.

Usage:
    python clean_zip.py input.csv ZipColumn
    python clean_zip.py input.csv ZipColumn output.csv

If no output file is provided, the script creates: input_cleaned.csv
"""

import sys
import re
from pathlib import Path
import pandas as pd


# Extract any digit sequence from a cell
ZIP_REGEX = re.compile(r"\d+")


# =============================
# Helpers
# =============================

def clean_zip(value):
    """
    Clean a ZIP code with the following rules:
      - Keep only digits
      - Use only the first 5 digits (ZIP+4 → ZIP)
      - Remove everything else
      - If no valid digits → return empty string
    """
    if pd.isna(value):
        return ""

    text = str(value).strip()

    # Extract all numeric sequences
    matches = ZIP_REGEX.findall(text)
    if not matches:
        return ""

    # Build a digit-only string
    digits = "".join(matches)

    # Only keep first 5 digits
    return digits[:5]


def read_csv_with_fallback(path: Path) -> pd.DataFrame:
    """Try several encodings to avoid decode errors."""
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin1"]
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            print(f"Loaded CSV using encoding: {enc}")
            return df
        except Exception:
            continue
    raise RuntimeError("Could not decode CSV with standard encodings.")


# =============================
# Cleaning
# =============================

def clean_dataframe(df: pd.DataFrame, zip_col: str) -> pd.DataFrame:
    """Clean only the specified ZIP column."""
    if zip_col not in df.columns:
        raise ValueError(f"Column '{zip_col}' not found in CSV.")

    print(f"Cleaning ZIP codes in column: {zip_col}")

    df[zip_col] = df[zip_col].apply(clean_zip)
    return df


# =============================
# Entrypoint
# =============================

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("   python clean_zip.py input.csv ZipColumn")
        print("   python clean_zip.py input.csv ZipColumn output.csv")
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()
    zip_column = sys.argv[2]

    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    if len(sys.argv) >= 4:
        output_path = Path(sys.argv[3]).resolve()
    else:
        output_path = input_path.with_name(
            f"{input_path.stem}_cleaned{input_path.suffix}"
        )

    df = read_csv_with_fallback(input_path)
    cleaned = clean_dataframe(df, zip_column)
    cleaned.to_csv(output_path, index=False)

    print(f"Cleaned file saved to: {output_path}")


if __name__ == "__main__":
    main()
