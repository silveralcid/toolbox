"""
clean_facebook.py – Normalize Facebook URLs and validate valid page/profile structure.

Usage:
    python clean_facebook.py input.csv
    python clean_facebook.py input.csv ColumnName
    python clean_facebook.py input.csv ColumnName output.csv

Rules:
    - Only valid Facebook URLs allowed
    - Must NOT be post/share/comment/photo/video/story links
    - Normalize:
        * remove http/https
        * keep www.
        * lowercase domain
        * remove trailing slash
    - Auto-detect columns containing "facebook", "fb", or "meta"
    - Output:
        {input_stem}_cleaned.csv
        clean_facebook_log.txt
"""

import sys
import re
from pathlib import Path
import pandas as pd
from urllib.parse import urlparse, parse_qs


# ==========================================================
# Allowed domains
# ==========================================================

FACEBOOK_DOMAINS = [
    "facebook.com",
    "www.facebook.com",
    "fb.com",
    "www.fb.com",
]

# ==========================================================
# Invalid path patterns (delete links)
# ==========================================================

INVALID_FACEBOOK_SEGMENTS = [
    "/posts/",
    "/post/",
    "/photos/",
    "/photo/",
    "/videos/",
    "/video/",
    "/reel/",
    "/story.php",
    "/share/",
    "/groups/",
    "/watch/",
]

# ==========================================================
# Valid root-level Facebook patterns
# ==========================================================

VALID_FACEBOOK_PATTERNS = [
    "/profile.php",
    "/people/",
    "/public/",
    "/pages/",
    "/pg/",
    "/business/",
    "/marketplace/",
    # Any other top-level root is allowed as long as it's not invalid
]


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


def normalize_facebook_url(value: str) -> str:
    """Normalize and validate Facebook URLs."""
    if pd.isna(value):
        return ""

    v = str(value).strip()
    if v == "":
        return ""

    v = v.replace(" ", "")

    # Add scheme if missing
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+\-.]*://", v):
        v_for_parse = "https://" + v
    else:
        v_for_parse = v

    try:
        parsed = urlparse(v_for_parse)
        domain = parsed.netloc.lower()
        path = parsed.path.rstrip("/")

        # Check domain
        if domain not in FACEBOOK_DOMAINS:
            return ""

        # Force www.
        if not domain.startswith("www."):
            domain = "www." + domain

        # Remove double slashes
        path = re.sub(r"//+", "/", path)

        # Reject invalid segments
        lowerpath = path.lower() + "/"
        for bad in INVALID_FACEBOOK_SEGMENTS:
            if bad in lowerpath:
                return ""

        # Accept basic root patterns
        valid = False

        # Patterns that should be explicitly allowed
        for ok in VALID_FACEBOOK_PATTERNS:
            if lowerpath.startswith(ok):
                valid = True
                break

        # For vanity usernames or page usernames:
        # Example: /acmecorp, /john.smith.123
        if not valid:
            # valid if it's exactly one path segment and not empty
            # /username
            parts = [p for p in path.split("/") if p != ""]
            if len(parts) == 1 and parts[0] not in ("home", "pages", "marketplace"):
                valid = True

        # If still not valid → delete
        if not valid:
            return ""

        # Build final clean URL
        cleaned = domain + path
        cleaned = re.sub(r"//+", "/", cleaned)

        return cleaned

    except Exception:
        return ""


def detect_facebook_columns(df: pd.DataFrame):
    """Auto-detect Facebook columns based on name."""
    return [
        c for c in df.columns
        if "facebook" in c.lower() or "fb" in c.lower() or "meta" in c.lower()
    ]


def write_log(log_path, columns_cleaned, changes):
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("CLEAN FACEBOOK LOG\n")
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
            cleaned = normalize_facebook_url(val)
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
        print("  python clean_facebook.py input.csv")
        print("  python clean_facebook.py input.csv ColumnName")
        print("  python clean_facebook.py input.csv ColumnName output.csv")
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Cannot find file: {input_path}")

    columns = []
    output_path = None

    # Collect column names until output is found
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.endswith(".csv"):
            output_path = Path(arg).resolve()
            break
        columns.append(arg)
        i += 1

    df = read_csv_with_fallback(input_path)

    # Auto-detect FB columns
    if not columns:
        columns = detect_facebook_columns(df)
        if not columns:
            raise ValueError("No Facebook columns found and none provided.")

    # Default output file
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_cleaned{input_path.suffix}")

    log_path = input_path.with_name("clean_facebook_log.txt")

    cleaned_df, changes = clean_dataframe(df, columns)

    cleaned_df.to_csv(output_path, index=False)
    write_log(log_path, columns, changes)

    print(f"Cleaned Facebook CSV saved to: {output_path}")
    print(f"Log saved to:                 {log_path}")


if __name__ == "__main__":
    main()