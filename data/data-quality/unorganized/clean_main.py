import sys
import subprocess
from pathlib import Path
import pandas as pd
import datetime


# ============================================================
# INTERNAL CONFIG (modify here)
# ============================================================

CONFIG = {
    "run_duplicate": True,
    "duplicate_args": ["Business_Name", "Business_Email", "Business_Website"],

    "run_phone": True,
    "phone_args": ["Business_Phone"],

    "run_zip": True,
    "zip_args": ["Business_Zip/Postal Code"],

    "run_state": True,
    "state_args": ["Business_State", "abbr"],

    "run_website": True,
    "website_args": ["Business_Website"],

    "run_email": True,
    "email_args": ["Business_Email"],

    "run_linkedin": True,
    "linkedin_args": ["Business_LinkedIn"],

    "run_facebook": True,
    "facebook_args": ["Business_Facebook"],

    "run_instagram": True,
    "instagram_args": ["Business_Instagram"],

    "run_number": True,
    "number_args": ["Distance", "decimal", "1", "round"],

    "run_alphanum": True,
    "alphanum_args": ["Business_City", "--keep", "-", "--replace", " "],

    "allow_cli_override": False,
}


# ============================================================
# Utility
# ============================================================

def run_script(script, input_csv, args):
    cmd = ["python", script, str(input_csv)] + args
    subprocess.run(cmd, check=True)


def write_main_log(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("CLEAN MAIN LOG\n")
        f.write("==============\n")
        f.write(f"Run time: {datetime.datetime.now()}\n\n")

        for line in lines:
            f.write(line + "\n")


def column_exists(csv_path: Path, col: str) -> bool:
    df = pd.read_csv(csv_path, encoding="latin1")  # safe fallback
    return col in df.columns


# ============================================================
# PIPELINE
# ============================================================

def main():

    if len(sys.argv) < 2:
        print("Usage: python clean_main.py input.csv")
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    main_log = []
    current_file = input_path
    step_index = 1

    pipeline = [
        ("clean_duplicate.py", "run_duplicate", "duplicate_args"),
        ("clean_phone.py", "run_phone", "phone_args"),
        ("clean_zip.py", "run_zip", "zip_args"),
        ("clean_state.py", "run_state", "state_args"),
        ("clean_website.py", "run_website", "website_args"),
        ("clean_email.py", "run_email", "email_args"),
        ("clean_linkedin.py", "run_linkedin", "linkedin_args"),
        ("clean_facebook.py", "run_facebook", "facebook_args"),
        ("clean_instagram.py", "run_instagram", "instagram_args"),
        ("clean_number.py", "run_number", "number_args"),
        ("clean_alphanum.py", "run_alphanum", "alphanum_args"),
    ]

    for script, run_key, args_key in pipeline:

        if not CONFIG[run_key]:
            main_log.append(f"[SKIP] {script} (disabled in config)")
            continue

        args = CONFIG[args_key]

        # Every tool's first argument is the column name
        col = args[0]

        # validate column exists
        if not column_exists(current_file, col):
            main_log.append(
                f"[SKIP] {script} — Column '{col}' not found in {current_file.name}"
            )
            continue

        main_log.append(f"[RUN ] Step {step_index}: {script} on {current_file.name}")
        main_log.append(f"       Args: {args}")

        # Run script
        run_script(script, current_file, args)

        # next output name
        next_file = current_file.with_name(
            f"{current_file.stem}_cleaned{current_file.suffix}"
        )

        if not next_file.exists():
            raise RuntimeError(f"Expected output missing: {next_file}")

        main_log.append(f"       Output: {next_file.name}\n")

        current_file = next_file
        step_index += 1

    main_log.append("=========================")
    main_log.append(f"FINAL OUTPUT: {current_file}")
    main_log.append("=========================")

    # save main log
    log_path = input_path.with_name("clean_main_log.txt")
    write_main_log(log_path, main_log)

    print("\n=== PIPELINE COMPLETE ===")
    print(f"Final cleaned file: {current_file}")
    print(f"Main log saved:     {log_path}")


if __name__ == "__main__":
    main()
