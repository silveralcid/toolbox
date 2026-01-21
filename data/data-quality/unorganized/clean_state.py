"""
clean_state.py – Normalize US state fields (abbreviation or full name).

Usage:
    python clean_state.py input.csv
    python clean_state.py input.csv full
    python clean_state.py input.csv ColumnName
    python clean_state.py input.csv ColumnName abbr/full
    python clean_state.py input.csv ColumnName abbr/full output.csv

If NO column name is provided:
    Automatically detect any column whose name contains:
    "state", "province", "state/province", "region", "st", etc.

Default mode:
    abbr

Output:
    {input_stem}_cleaned.csv
    clean_state_log.txt
"""

import sys
from pathlib import Path
import pandas as pd


# ============================================================
# State mappings
# ============================================================

STATE_TO_ABBR = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
    "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT",
    "DELAWARE": "DE", "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI",
    "IDAHO": "ID", "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA",
    "KANSAS": "KS", "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME",
    "MARYLAND": "MD", "MASSACHUSETTS": "MA", "MICHIGAN": "MI",
    "MINNESOTA": "MN", "MISSISSIPPI": "MS", "MISSOURI": "MO",
    "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM",
    "NEW YORK": "NY", "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND",
    "OHIO": "OH", "OKLAHOMA": "OK", "OREGON": "OR",
    "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC", "SOUTH DAKOTA": "SD", "TENNESSEE": "TN",
    "TEXAS": "TX", "UTAH": "UT", "VERMONT": "VT", "VIRGINIA": "VA",
    "WASHINGTON": "WA", "WEST VIRGINIA": "WV", "WISCONSIN": "WI",
    "WYOMING": "WY",
}

ABBR_TO_STATE = {abbr: name for name, abbr in STATE_TO_ABBR.items()}


# ============================================================
# Helpers
# ============================================================

def normalize_state_name(value: str) -> str:
    return str(value).strip().upper()


def clean_state(value, mode):
    if pd.isna(value):
        return ""

    text = normalize_state_name(value)

    if text in STATE_TO_ABBR:
        abbr = STATE_TO_ABBR[text]
        return abbr if mode == "abbr" else text.title()

    if text in ABBR_TO_STATE:
        full = ABBR_TO_STATE[text]
        return text if mode == "abbr" else full.title()

    return ""


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


# ============================================================
# Column auto-detection
# ============================================================

STATE_KEYWORDS = [
    "state", "province", "state/province", "region"
]

def detect_state_columns(df: pd.DataFrame):
    cols = []
    for col in df.columns:
        cname = col.lower()
        for kw in STATE_KEYWORDS:
            if kw in cname:
                cols.append(col)
                break
    return cols


# ============================================================
# Logging
# ============================================================

def write_log(path, columns, mode, changes):
    with open(path, "w", encoding="utf-8") as f:
        f.write("CLEAN STATE LOG\n")
        f.write("================\n\n")

        f.write(f"Mode: {mode}\n\n")
        f.write("Columns cleaned:\n")
        for c in columns:
            f.write(f"  - {c}\n")

        f.write(f"\nTotal changed rows: {len(changes)}\n\n")

        f.write("Changed entries:\n")
        f.write("----------------\n")
        if not changes:
            f.write("No values changed.\n")
        else:
            for old, new, col in changes:
                f.write(f"[{col}] {old} → {new}\n")


# ============================================================
# Cleaning
# ============================================================

def clean_dataframe(df, columns, mode):
    changes = []
    for col in columns:
        def clean_cell(val):
            cleaned = clean_state(val, mode)
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
        print("  python clean_state.py input.csv")
        print("  python clean_state.py input.csv full")
        print("  python clean_state.py input.csv ColumnName")
        print("  python clean_state.py input.csv ColumnName abbr/full")
        print("  python clean_state.py input.csv ColumnName abbr/full output.csv")
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Cannot find: {input_path}")

    args = sys.argv[2:]

    columns = []
    mode = None
    output_path = None

    for arg in args:
        if arg.lower() in ("abbr", "full"):
            mode = arg.lower()
        elif arg.endswith(".csv"):
            output_path = Path(arg).resolve()
        else:
            columns.append(arg)

    # Default mode = abbr
    if mode is None:
        mode = "abbr"
        print("No mode provided → defaulting to: abbr")

    df = read_csv_with_fallback(input_path)

    # Auto-detect columns
    if not columns:
        columns = detect_state_columns(df)
        if not columns:
            raise ValueError("No state-related columns found and none provided.")

    # Output default
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_cleaned{input_path.suffix}")

    log_path = input_path.with_name("clean_state_log.txt")

    cleaned_df, changes = clean_dataframe(df, columns, mode)
    cleaned_df.to_csv(output_path, index=False)
    write_log(log_path, columns, mode, changes)

    print(f"Cleaned file saved to: {output_path}")
    print(f"Log file saved to:   {log_path}")


if __name__ == "__main__":
    main()
