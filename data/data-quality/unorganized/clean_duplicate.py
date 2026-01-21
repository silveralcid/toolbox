"""
clean_duplicate.py – Remove duplicates based on selected columns.

Usage:
    python clean_duplicate.py input.csv col1 col2 col3
    python clean_duplicate.py input.csv col1 col2 col3 output.csv

Output:
    {input_name}_cleaned.csv
    clean_duplicate_log.txt (same folder)
"""

import sys
from pathlib import Path
import pandas as pd


# =============================================================
# Helpers
# =============================================================

def read_csv_with_fallback(path: Path) -> pd.DataFrame:
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
# Deduplication
# =============================================================

def dedupe_dataframe(df: pd.DataFrame, cols):
    """
    Returns:
        deduped_df
        removed_df
    """
    print(f"Deduplicating based on: {', '.join(cols)}")

    before = len(df)

    deduped = df.drop_duplicates(subset=cols, keep="first")
    after = len(deduped)

    removed_count = before - after
    removed_rows = df[df.duplicated(subset=cols, keep="first")]

    return deduped, removed_rows, before, after, removed_count


def write_log(log_path, before, after, removed_count, removed_rows):
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("CLEAN DUPLICATE LOG\n")
        f.write("=====================\n\n")
        f.write(f"Rows before: {before}\n")
        f.write(f"Rows after:  {after}\n")
        f.write(f"Rows removed: {removed_count}\n\n")

        f.write("Removed rows:\n")
        f.write("---------------------\n")

        if removed_count == 0:
            f.write("No duplicates removed.\n")
        else:
            f.write(removed_rows.to_string(index=False))
            f.write("\n")


# =============================================================
# Entrypoint
# =============================================================

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("   python clean_duplicate.py input.csv col1 col2 col3")
        print("   python clean_duplicate.py input.csv col1 col2 col3 output.csv")
        sys.exit(1)

    # Required input
    input_path = Path(sys.argv[1]).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"File does not exist: {input_path}")

    # Parse columns
    columns = []
    i = 2
    output_path = None

    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg.endswith(".csv"):
            output_path = Path(arg).resolve()
            break

        columns.append(arg)
        i += 1

    if not columns:
        raise ValueError("You must specify at least one column to dedupe on.")

    # Default output name
    if output_path is None:
        output_path = input_path.with_name(
            f"{input_path.stem}_cleaned{input_path.suffix}"
        )

    log_path = input_path.with_name("clean_duplicate_log.txt")

    # Load + Process
    df = read_csv_with_fallback(input_path)
    deduped, removed_rows, before, after, removed_count = dedupe_dataframe(df, columns)

    # Save outputs
    deduped.to_csv(output_path, index=False)
    write_log(log_path, before, after, removed_count, removed_rows)

    print(f"Cleaned CSV saved to: {output_path}")
    print(f"Log file saved to:   {log_path}")


if __name__ == "__main__":
    main()
