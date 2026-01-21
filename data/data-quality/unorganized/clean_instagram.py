"""
clean_instagram.py – Normalize Instagram URLs and user handles.

Usage:
    python clean_instagram.py input.csv
    python clean_instagram.py input.csv ColumnName
    python clean_instagram.py input.csv ColumnName output.csv

Rules:
    - Only valid Instagram profile URLs allowed
    - Remove post/reel/story/direct/etc URLs
    - If cell is just a handle (acmecorp, @acmecorp), convert to:
        www.instagram.com/acmecorp
    - Normalize:
        * remove http/https
        * force www.instagram.com
        * lowercase domain
        * remove trailing slash
    - Auto-detect columns containing "instagram", "ig", or "insta"
    - Output:
        {input_stem}_cleaned.csv
        clean_instagram_log.txt
"""

import sys
import re
from pathlib import Path
import pandas as pd
from urllib.parse import urlparse


# ==========================================================
# Allowed Instagram domains
# ==========================================================

INSTAGRAM_DOMAINS = [
    "instagram.com",
    "www.instagram.com",
]


# ==========================================================
# Segments that must NOT appear (invalid IG links)
# ==========================================================

INVALID_INSTAGRAM_SEGMENTS = [
    "/p/",
    "/reel/",
    "/reels/",
    "/tv/",
    "/stories/",
    "/story/",
    "/s/",
    "/explore/",
    "/direct/",
    "/tags/",
    "/challenge/",
]


# ==========================================================
# Detect usernames
# ==========================================================

USERNAME_REGEX = re.compile(r"^@?([A-Za-z0-9._]{1,30})$")


# ==========================================================
# Helpers
# ==========================================================

def read_csv_with_fallback(path: Path) -> pd.DataFrame:
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            print(f"Loaded CSV using encoding: {enc}")
            return df
        except Exception:
            continue
    raise RuntimeError("Could not decode CSV using known encodings.")


def normalize_instagram(value: str) -> str:
    """Normalize Instagram links OR convert plain usernames into valid IG URLs."""
    if pd.isna(value):
        return ""

    v = str(value).strip()
    if v == "":
        return ""

    # Remove spaces
    v = v.replace(" ", "")

    # ----------------------------------------------------------
    # 1. If it's a username only (@optional)
    # ----------------------------------------------------------
    m = USERNAME_REGEX.match(v)
    if m:
        username = m.group(1)
        return f"www.instagram.com/{username}"

    # ----------------------------------------------------------
    # 2. Treat as URL
    # ----------------------------------------------------------
    # Add scheme if missing
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+\-.]*://", v):
        v_for_parse = "https://" + v
    else:
        v_for_parse = v

    try:
        parsed = urlparse(v_for_parse)
        domain = parsed.netloc.lower()
        path = parsed.path.rstrip("/")

        # Domain must be Instagram
        if domain not in INSTAGRAM_DOMAINS:
            return ""

        # Force correct domain
        domain = "www.instagram.com"

        # Collapse multiple slashes
        path = re.sub(r"//+", "/", path)

        lowerpath = path.lower() + "/"
        for bad in INVALID_INSTAGRAM_SEGMENTS:
            if bad in lowerpath:
                return ""

        # Extract username from path
        parts = [p for p in path.split("/") if p]
        if len(parts) != 1:
            return ""

        username = parts[0]

        # Validate username
        if not USERNAME_REGEX.match(username):
            return ""

        cleaned = f"{domain}/{username}"
        return cleaned

    except Exception:
        return ""


def detect_instagram_columns(df: pd.DataFrame):
    """Auto-detect Instagram columns."""
    return [
        c for c in df.columns
        if "instagram" in c.lower() or "insta" in c.lower() or c.lower().startswith("ig")
    ]


def write_log(log_path, columns_cleaned, changes):
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("CLEAN INSTAGRAM LOG\n")
        f.write("====================\n\n")

        f.write("Columns cleaned:\n")
        for c in columns_cleaned:
            f.write(f"  - {c}\n")
        f.write("\n")

        f.write("Changed values:\n")
        f.write("-----------------------\n")
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
            cleaned = normalize_instagram(val)
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
        print("  python clean_instagram.py input.csv")
        print("  python clean_instagram.py input.csv ColumnName")
        print("  python clean_instagram.py input.csv ColumnName output.csv")
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Cannot find file: {input_path}")

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

    # Auto-detect IG columns
    if not columns:
        columns = detect_instagram_columns(df)
        if not columns:
            raise ValueError("No Instagram columns found and none provided.")

    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_cleaned{input_path.suffix}")

    log_path = input_path.with_name("clean_instagram_log.txt")

    cleaned_df, changes = clean_dataframe(df, columns)
    cleaned_df.to_csv(output_path, index=False)
    write_log(log_path, columns, changes)

    print(f"Cleaned Instagram CSV saved to: {output_path}")
    print(f"Log saved to:                  {log_path}")


if __name__ == "__main__":
    main()
