"""
clean_number.py – Clean numeric columns.

Features:
- Remove letters, whitespace, non-numerical characters
- Multiple columns supported
- Two modes:
    integer  (default)
    decimal
- Decimal controls:
    --places N
    --round up|down
- CLI:
    python clean_number.py input.csv col1 col2
    python clean_number.py input.csv col1 col2 --mode decimal --places 3 --round down output.csv
"""

import sys
import re
import math
from pathlib import Path
import pandas as pd


# =============================================================
# Default Settings
# =============================================================

DEFAULT_MODE = "integer"      # integer | decimal
DEFAULT_DECIMAL_PLACES = 2    # used only if mode=decimal and no --places given
DEFAULT_ROUND_MODE = "up"     # up | down


# =============================================================
# Helpers
# =============================================================

NON_NUMERIC_REGEX = re.compile(r"[^0-9\.]")  # allow only digits + dot


def extract_number(raw: str):
    """Strip everything except digits and at most ONE decimal point."""
    if pd.isna(raw):
        return ""

    text = str(raw).strip()
    if text == "":
        return ""

    # Remove all invalid characters
    cleaned = NON_NUMERIC_REGEX.sub("", text)

    # If more than one ".", keep only the first
    if cleaned.count(".") > 1:
        parts = cleaned.split(".")
        cleaned = parts[0] + "." + "".join(parts[1:])

    return cleaned


def convert_number(value: str, mode: str, places: int, round_mode: str):
    """Convert cleaned string into proper numeric output."""
    if value == "":
        return ""

    try:
        num = float(value)
    except Exception:
        return ""

    if mode == "integer":
        # Integer mode ignores decimals and rounding mode
        return str(int(num))

    # Decimal mode
    multiplier = 10 ** places

    if round_mode == "up":
        num = math.ceil(num * multiplier) / multiplier
    elif round_mode == "down":
        num = math.floor(num * multiplier) / multiplier

    # Format with exact decimal places
    fmt = "{:." + str(places) + "f}"
    return fmt.format(num)


def read_csv_with_fallback(path: Path) -> pd.DataFrame:
    """Try several encodings so CSV won't break."""
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin1"]
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            print(f"Loaded CSV using encoding: {enc}")
            return df
        except Exception:
            continue
    raise RuntimeError("Could not decode CSV with standard encodings.")


# =============================================================
# Cleaning
# =============================================================

def clean_dataframe(df: pd.DataFrame, columns, mode, places, round_mode):
    """Clean specified numeric columns."""
    print(f"Cleaning columns: {', '.join(columns)}")
    print(f"Mode: {mode}, Places: {places}, Rounding: {round_mode}")

    for col in columns:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in CSV.")

        df[col] = df[col].apply(lambda v: convert_number(
            extract_number(v),
            mode,
            places,
            round_mode,
        ))

    return df


# =============================================================
# Entrypoint
# =============================================================

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python clean_number.py input.csv col1 col2 col3 [options] [output.csv]")
        print("\nOptions:")
        print("  --mode integer|decimal")
        print("  --places N      (default = 2 when decimal mode)")
        print("  --round up|down (default = up)")
        sys.exit(1)

    # Required
    input_path = Path(sys.argv[1]).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Parse positional columns until an option flag is detected
    columns = []
    i = 2
    while i < len(sys.argv) and not sys.argv[i].startswith("--"):
        # Stop before the final argument if it's output.csv
        if i == len(sys.argv) - 1 and sys.argv[i].endswith(".csv"):
            break
        columns.append(sys.argv[i])
        i += 1

    # Defaults
    mode = DEFAULT_MODE
    places = DEFAULT_DECIMAL_PLACES
    round_mode = DEFAULT_ROUND_MODE
    output_path = None

    # Parse options
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == "--mode":
            i += 1
            mode = sys.argv[i].lower()
        elif arg == "--places":
            i += 1
            places = int(sys.argv[i])
        elif arg == "--round":
            i += 1
            round_mode = sys.argv[i].lower()
        else:
            # If it ends with .csv → treat as output
            if arg.endswith(".csv"):
                output_path = Path(arg).resolve()
            else:
                print(f"Unknown argument ignored: {arg}")
        i += 1

    # Validate
    if mode not in ("integer", "decimal"):
        raise ValueError("Mode must be 'integer' or 'decimal'.")

    if round_mode not in ("up", "down"):
        raise ValueError("Round mode must be 'up' or 'down'.")

    # Auto-output file if not provided
    if output_path is None:
        output_path = input_path.with_name(
            f"{input_path.stem}_cleaned{input_path.suffix}"
        )

    df = read_csv_with_fallback(input_path)
    cleaned = clean_dataframe(df, columns, mode, places, round_mode)
    cleaned.to_csv(output_path, index=False)

    print(f"Cleaned file saved to: {output_path}")


if __name__ == "__main__":
    main()
