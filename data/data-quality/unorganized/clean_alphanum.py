"""
clean_alphanum.py – Remove or replace non-alphanumeric characters in specified columns.
Spaces are allowed by default.

Usage:
    python clean_alphanum.py input.csv Column1 Column2 ...
    python clean_alphanum.py input.csv Column1 Column2 ... output.csv
    python clean_alphanum.py input.csv Column1 Column2 ... --keep "-._"
    python clean_alphanum.py input.csv Column1 Column2 ... --replace "_"
    python clean_alphanum.py input.csv Column1 Column2 ... --strip-alpha
    python clean_alphanum.py input.csv Column1 Column2 ... --strip-num
    python clean_alphanum.py input.csv Column1 Column2 ... --keep "-" --replace " " output.csv

Rules:
    - REQUIRED: at least one column name
    - Default allowed characters: A-Z, a-z, 0-9, space
    - Optional: --keep "<chars>" allows additional characters
    - Optional: --replace "<char>" replacement for removed characters (default = "")
    - Optional: --strip-alpha removes all letters
    - Optional: --strip-num removes all digits
    - Produces log file: clean_alphanum_log.txt
"""

import sys
import re
from pathlib import Path
import pandas as pd


# ============================================================
# Helpers
# ============================================================

def read_csv_with_fallback(path: Path) -> pd.DataFrame:
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            print(f"Loaded using encoding: {enc}")
            return df
        except Exception:
            continue
    raise RuntimeError("Could not decode CSV.")


def build_cleaner(extra_chars: str):
    """Build regex to remove characters NOT allowed."""
    safe_extra = re.escape(extra_chars)
    pattern = rf"[^A-Za-z0-9 {safe_extra}]"
    return re.compile(pattern)


def apply_strip_modes(val, strip_alpha, strip_num):
    """Remove alpha or numeric characters before secondary cleaning."""
    if pd.isna(val):
        return val
    s = str(val)
    if strip_alpha:
        s = re.sub(r"[A-Za-z]", "", s)
    if strip_num:
        s = re.sub(r"[0-9]", "", s)
    return s


def clean_value(val, cleaner_regex, replacement, strip_alpha, strip_num):
    if pd.isna(val):
        return val

    # Apply alpha/numeric stripping first
    v = apply_strip_modes(val, strip_alpha, strip_num)

    # Remove unwanted characters
    cleaned = cleaner_regex.sub(replacement, v)
    return cleaned


def write_log(path, columns, changes):
    with open(path, "w", encoding="utf-8") as f:
        f.write("CLEAN ALPHANUM LOG\n")
        f.write("===================\n\n")

        f.write("Columns cleaned:\n")
        for col in columns:
            f.write(f"  - {col}\n")

        f.write(f"\nTotal changed entries: {len(changes)}\n\n")

        f.write("Changed values:\n")
        f.write("-----------------------\n")
        if not changes:
            f.write("No values changed.\n")
        else:
            for old, new, col in changes:
                f.write(f"[{col}] {old} → {new}\n")


# ============================================================
# Cleaning Logic
# ============================================================

def clean_dataframe(df, columns, regex, replacement, strip_alpha, strip_num):
    changes = []

    for col in columns:
        def apply_clean(val):
            newval = clean_value(val, regex, replacement, strip_alpha, strip_num)
            if str(val) != newval:
                changes.append((str(val), newval, col))
            return newval

        df[col] = df[col].apply(apply_clean)

    return df, changes


# ============================================================
# Entrypoint
# ============================================================

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python clean_alphanum.py input.csv Column1 Column2 ...")
        print("  python clean_alphanum.py input.csv Column1 Column2 ... output.csv")
        print('  python clean_alphanum.py input.csv Column1 --keep "-._"')
        print('  python clean_alphanum.py input.csv Column1 --replace "_"')
        print('  python clean_alphanum.py input.csv Column1 --strip-alpha')
        print('  python clean_alphanum.py input.csv Column1 --strip-num')
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Cannot find file: {input_path}")

    args = sys.argv[2:]

    columns = []
    output_path = None
    extra_chars = ""
    replacement = ""
    strip_alpha = False
    strip_num = False

    i = 0
    while i < len(args):
        arg = args[i]

        if arg == "--keep":
            i += 1
            if i >= len(args):
                raise ValueError("Missing characters after --keep")
            extra_chars = args[i]

        elif arg == "--replace":
            i += 1
            if i >= len(args):
                raise ValueError("Missing replacement after --replace")
            replacement = args[i]

        elif arg == "--strip-alpha":
            strip_alpha = True

        elif arg == "--strip-num":
            strip_num = True

        elif arg.endswith(".csv"):
            output_path = Path(arg).resolve()

        else:
            columns.append(arg)

        i += 1

    if not columns:
        raise ValueError("You must specify at least one column name.")

    regex = build_cleaner(extra_chars)
    df = read_csv_with_fallback(input_path)

    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_cleaned{input_path.suffix}")

    log_path = input_path.with_name("clean_alphanum_log.txt")

    cleaned_df, changes = clean_dataframe(df, columns, regex, replacement, strip_alpha, strip_num)
    cleaned_df.to_csv(output_path, index=False)
    write_log(log_path, columns, changes)

    print(f"Cleaned CSV saved to: {output_path}")
    print(f"Log saved to:         {log_path}")


if __name__ == "__main__":
    main()